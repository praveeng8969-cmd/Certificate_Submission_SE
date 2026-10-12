import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import update
from fastapi import HTTPException, status

from app.models.user import User
from app.models.resource import Resource
from app.models.request import ServiceRequest
from app.models.history import RequestStatusHistory
from app.schemas.schemas import RequestCreateSchema
from app.services.validation_service import ValidationService


class RequestService:
    @staticmethod
    def get_user_requests(db: Session, user_id: str) -> List[ServiceRequest]:
        return db.query(ServiceRequest).filter(
            ServiceRequest.user_id == user_id
        ).order_by(ServiceRequest.created_at.desc()).all()

    @staticmethod
    def get_all_requests(db: Session) -> List[ServiceRequest]:
        return db.query(ServiceRequest).order_by(
            ServiceRequest.created_at.desc()
        ).all()

    @staticmethod
    def get_request_by_id(db: Session, request_id: str) -> Optional[ServiceRequest]:
        return db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()

    @staticmethod
    def create_request(
        db: Session,
        user_id: str,
        payload: RequestCreateSchema,
        idempotency_key: str
    ) -> Tuple[ServiceRequest, bool]:
        """
        Atomically processes request creation with idempotency guard.
        Returns (ServiceRequest, is_duplicate).
        """
        # 1. Idempotency Check
        existing = db.query(ServiceRequest).filter(
            ServiceRequest.idempotency_key == idempotency_key
        ).first()
        if existing:
            # Retrying the same submission: return existing without double-reserving
            return existing, True

        # 2. Input Field Validation (BR5)
        valid_details, err_msg = ValidationService.validate_details(
            name=payload.name,
            phone=payload.phone,
            description=payload.description,
            reference=payload.reference
        )
        if not valid_details:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )

        # 3. User check and active limit validation (BR1, BR2)
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User '{user_id}' is inactive or does not exist."
            )

        valid_limit, limit_msg = ValidationService.validate_request_limit(user_id, db)
        if not valid_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=limit_msg
            )

        # 4. Resource check (BR2)
        resource = db.query(Resource).filter(Resource.id == payload.resource_id).first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{payload.resource_id}' not found."
            )

        valid_res, res_msg = ValidationService.validate_eligibility(user, resource)
        if not valid_res:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res_msg
            )

        # 5. Calculate charge (BR4)
        base_val = payload.base_value if payload.base_value is not None else Decimal("0.00")
        service_charge = ValidationService.calculate_charge(resource, base_val)

        # 6. Atomic Transaction: Reserve capacity and persist request + snapshot + history (BR7, BR3)
        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        snapshot = {
            "request_id": request_id,
            "applicant_name": payload.name,
            "phone": payload.phone,
            "description": payload.description,
            "reference": payload.reference,
            "base_value": str(base_val),
            "service_charge": str(service_charge),
            "resource_id": resource.id,
            "resource_service_name": resource.service_name,
            "resource_charge_applicable": resource.charge_applicable,
            "snapshot_timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Atomic conditional update of capacity
            stmt = (
                update(Resource)
                .where(Resource.id == resource.id, Resource.capacity > 0)
                .values(capacity=Resource.capacity - 1, updated_at=datetime.now(timezone.utc))
            )
            result = db.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Capacity for certificate '{resource.id}' was exhausted or unavailable."
                )

            # Insert ServiceRequest
            new_req = ServiceRequest(
                id=request_id,
                user_id=user_id,
                resource_id=resource.id,
                name=payload.name,
                phone=payload.phone,
                description=payload.description,
                reference=payload.reference,
                base_value=base_val,
                service_charge=service_charge,
                status="SUBMITTED",
                snapshot_data=snapshot,
                idempotency_key=idempotency_key,
                resource_reserved=True,
                resource_released=False
            )
            db.add(new_req)
            db.flush()  # Ensures new_req.id is populated for foreign key

            # Insert Status History
            history = RequestStatusHistory(
                reference_id=new_req.id,
                actor_id=user_id,
                old_status=None,
                new_status="SUBMITTED"
            )
            db.add(history)

            db.commit()
            db.refresh(new_req)
            return new_req, False

        except Exception as e:
            db.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Atomic transaction failed: {str(e)}"
            )

    @staticmethod
    def advance_status(
        db: Session,
        request_id: str,
        actor_id: str,
        target_status: str
    ) -> ServiceRequest:
        """
        Administrator workflow advancement (BR8, BR10).
        Enforces SUBMITTED -> APPROVED -> IN_PROGRESS -> COMPLETED.
        """
        actor = db.query(User).filter(User.id == actor_id).first()
        if not actor or actor.role != "ADMINISTRATOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only Administrators can advance request status."
            )

        req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request '{request_id}' not found."
            )

        valid_trans, trans_msg = ValidationService.validate_transition(
            current_status=req.status,
            target_status=target_status,
            actor_role=actor.role
        )
        if not valid_trans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=trans_msg
            )

        try:
            old_st = req.status
            req.status = target_status
            req.updated_at = datetime.now(timezone.utc)

            history = RequestStatusHistory(
                reference_id=req.id,
                actor_id=actor_id,
                old_status=old_st,
                new_status=target_status
            )
            db.add(history)
            db.commit()
            db.refresh(req)
            return req
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to advance status: {str(e)}"
            )

    @staticmethod
    def cancel_request(
        db: Session,
        request_id: str,
        user_id: str
    ) -> ServiceRequest:
        """
        User cancellation (BR8, BR9, BR10).
        Can only cancel SUBMITTED requests.
        Must release reserved resource capacity exactly once.
        Repeated cancellation must be rejected.
        """
        req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request '{request_id}' not found."
            )

        # Ownership authorization check (BR10)
        if req.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only cancel your own requests."
            )

        # Repeated cancellation or invalid state check (BR8, BR9)
        if req.status == "CANCELLED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request has already been cancelled. Repeated cancellation is rejected."
            )

        if req.status != "SUBMITTED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel request in '{req.status}' status. Only SUBMITTED requests are eligible for cancellation."
            )

        try:
            old_st = req.status
            req.status = "CANCELLED"
            req.updated_at = datetime.now(timezone.utc)

            # Release capacity exactly once if reserved and not yet released
            if req.resource_reserved and not req.resource_released:
                stmt = (
                    update(Resource)
                    .where(Resource.id == req.resource_id)
                    .values(capacity=Resource.capacity + 1, updated_at=datetime.now(timezone.utc))
                )
                db.execute(stmt)
                req.resource_released = True
                req.resource_reserved = False

            history = RequestStatusHistory(
                reference_id=req.id,
                actor_id=user_id,
                old_status=old_st,
                new_status="CANCELLED"
            )
            db.add(history)
            db.commit()
            db.refresh(req)
            return req
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel request: {str(e)}"
            )
