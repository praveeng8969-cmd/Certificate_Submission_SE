from typing import List, Optional
from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.schemas import UserOut

router = APIRouter(prefix="/api/auth", tags=["Authentication & Role Selection"])


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Identifies active actor via:
    1. Header 'X-User-Id'
    2. Cookie 'session_user_id'
    3. Query parameter 'user_id'
    4. Default fallback: 'U001'
    """
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        user_id = request.cookies.get("session_user_id")
    if not user_id:
        user_id = request.query_params.get("user_id")
    if not user_id:
        user_id = "U001"

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Fallback to U001 if specific user not found
        user = db.query(User).filter(User.id == "U001").first()
    if not user:
        raise HTTPException(status_code=401, detail="User account not found.")
    return user


@router.get("/accounts", response_model=List[UserOut])
def list_accounts(db: Session = Depends(get_db)):
    """List all synthetic demo accounts."""
    return db.query(User).all()


@router.get("/current", response_model=UserOut)
def get_current_account(current_user: User = Depends(get_current_user)):
    """Return currently active user profile."""
    return current_user


@router.post("/select/{user_id}", response_model=UserOut)
def select_account(
    user_id: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Switch active account and set simulated session cookie."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Account '{user_id}' not found.")
    
    response.set_cookie(key="session_user_id", value=user.id, path="/", httponly=False)
    return user
