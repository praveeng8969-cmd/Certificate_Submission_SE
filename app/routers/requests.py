from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.resource import Resource
from app.schemas.schemas import (
    ResourceOut,
    ChargePreviewRequest,
    ChargePreviewResponse,
    RequestCreateSchema,
    ServiceRequestOut,
)
from app.services.validation_service import ValidationService
from app.services.request_service import RequestService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/requests", tags=["Requests"])


@router.get("/services", response_model=List[ResourceOut])
def list_services(db: Session = Depends(get_db)):
    """List all certificate services in catalog with capacity and status."""
    return db.query(Resource).all()


@router.post("/preview-charge", response_model=ChargePreviewResponse)
def preview_charge(
    payload: ChargePreviewRequest,
    db: Session = Depends(get_db)
):
    """
    BR4: Calculate applicable fee preview dynamically:
    - Base value < 1000 => 50
    - Base value >= 1000 => 0
    - Non-chargeable => 0
    """
    resource = db.query(Resource).filter(Resource.id == payload.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    base_val = payload.base_value if payload.base_value is not None else Decimal("0.00")
    charge = ValidationService.calculate_charge(resource, base_val)

    if not resource.charge_applicable:
        explanation = "Service has no chargeable amount applied (₹0.00)."
    elif base_val < Decimal("1000.00"):
        explanation = "Base value is below ₹1,000.00: standard service charge of ₹50.00 applies."
    else:
        explanation = "Base value is ₹1,000.00 or above: service charge is waived (₹0.00)."

    return ChargePreviewResponse(
        resource_id=resource.id,
        charge_applicable=resource.charge_applicable,
        base_value=base_val,
        calculated_charge=charge,
        explanation=explanation
    )


@router.post("/validate")
def validate_request_inputs(
    payload: RequestCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validates form data prior to submission without changing database state.
    """
    valid_details, msg = ValidationService.validate_details(
        name=payload.name,
        phone=payload.phone,
        description=payload.description,
        reference=payload.reference
    )
    if not valid_details:
        raise HTTPException(status_code=400, detail=msg)

    valid_limit, l_msg = ValidationService.validate_request_limit(current_user.id, db)
    if not valid_limit:
        raise HTTPException(status_code=400, detail=l_msg)

    resource = db.query(Resource).filter(Resource.id == payload.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Requested resource not found")

    valid_elig, e_msg = ValidationService.validate_eligibility(current_user, resource)
    if not valid_elig:
        raise HTTPException(status_code=400, detail=e_msg)

    charge = ValidationService.calculate_charge(resource, payload.base_value)

    return {
        "valid": True,
        "calculated_charge": float(charge),
        "message": "All validations passed. Ready for submission."
    }


@router.post("/submit", response_model=ServiceRequestOut, status_code=status.HTTP_201_CREATED)
def submit_request(
    payload: RequestCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atomic submission with idempotency protection (BR6, BR7).
    """
    req, is_dup = RequestService.create_request(
        db=db,
        user_id=current_user.id,
        payload=payload,
        idempotency_key=payload.idempotency_key
    )
    return req


@router.get("/my", response_model=List[ServiceRequestOut])
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    BR10: Users may view only their own requests.
    """
    return RequestService.get_user_requests(db=db, user_id=current_user.id)


@router.get("/{request_id}", response_model=ServiceRequestOut)
def get_request_details(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    BR10: Request details viewable by owner or administrator.
    """
    req = RequestService.get_request_by_id(db=db, request_id=request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    
    if current_user.role != "ADMINISTRATOR" and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this request.")
    
    return req


@router.post("/{request_id}/cancel", response_model=ServiceRequestOut)
def cancel_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    BR8, BR9, BR10: User cancellation of SUBMITTED request.
    Releases reserved capacity exactly once.
    """
    return RequestService.cancel_request(
        db=db,
        request_id=request_id,
        user_id=current_user.id
    )
