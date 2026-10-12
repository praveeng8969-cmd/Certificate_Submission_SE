from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.schemas import ServiceRequestOut, AdvanceStatusSchema
from app.services.request_service import RequestService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Administrator Operations"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMINISTRATOR":
        raise HTTPException(
            status_code=403,
            detail="Access denied: Administrator privileges required."
        )
    return current_user


@router.get("/requests", response_model=List[ServiceRequestOut])
def list_all_requests(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Administrator: View all certificate requests in the system."""
    return RequestService.get_all_requests(db=db)


@router.post("/requests/{request_id}/advance", response_model=ServiceRequestOut)
def advance_request_status(
    request_id: str,
    payload: AdvanceStatusSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Administrator: Advance request sequentially:
    SUBMITTED -> APPROVED -> IN_PROGRESS -> COMPLETED
    """
    return RequestService.advance_status(
        db=db,
        request_id=request_id,
        actor_id=admin.id,
        target_status=payload.target_status
    )
