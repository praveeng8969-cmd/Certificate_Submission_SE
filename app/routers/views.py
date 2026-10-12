from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.resource import Resource
from app.models.request import ServiceRequest
from app.services.request_service import RequestService
from app.routers.auth import get_current_user

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(include_in_schema=False)


def get_all_users(db: Session):
    return db.query(User).all()


@router.get("/", response_class=HTMLResponse)
def index_redirect(
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "ADMINISTRATOR":
        return RedirectResponse(url="/admin", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/accounts", response_class=HTMLResponse)
def view_accounts(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    all_users = get_all_users(db)
    return templates.TemplateResponse(
        "account_select.html",
        {
            "request": request,
            "current_user": current_user,
            "all_users": all_users,
            "active_page": "accounts"
        }
    )


@router.get("/dashboard", response_class=HTMLResponse)
def view_user_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "ADMINISTRATOR":
        return RedirectResponse(url="/admin", status_code=302)

    all_users = get_all_users(db)
    user_requests = RequestService.get_user_requests(db, current_user.id)
    services = db.query(Resource).all()

    total = len(user_requests)
    active = len([r for r in user_requests if r.status in ["SUBMITTED", "APPROVED", "IN_PROGRESS"]])
    completed = len([r for r in user_requests if r.status == "COMPLETED"])
    cancelled = len([r for r in user_requests if r.status == "CANCELLED"])

    stats = {
        "total": total,
        "active": active,
        "completed": completed,
        "cancelled": cancelled
    }

    return templates.TemplateResponse(
        "user_dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "all_users": all_users,
            "services": services,
            "recent_requests": user_requests[:5],
            "stats": stats,
            "active_page": "dashboard"
        }
    )


@router.get("/requests/new", response_class=HTMLResponse)
def view_create_request(
    request: Request,
    resource_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "ADMINISTRATOR":
        return RedirectResponse(url="/admin", status_code=302)

    all_users = get_all_users(db)
    services = db.query(Resource).all()
    user_requests = RequestService.get_user_requests(db, current_user.id)
    active_count = len([r for r in user_requests if r.status in ["SUBMITTED", "APPROVED", "IN_PROGRESS"]])

    return templates.TemplateResponse(
        "create_request.html",
        {
            "request": request,
            "current_user": current_user,
            "all_users": all_users,
            "services": services,
            "selected_resource_id": resource_id or (services[0].id if services else ""),
            "active_count": active_count,
            "active_page": "create"
        }
    )


@router.get("/requests/my", response_class=HTMLResponse)
def view_my_requests(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    all_users = get_all_users(db)
    user_requests = RequestService.get_user_requests(db, current_user.id)

    return templates.TemplateResponse(
        "my_requests.html",
        {
            "request": request,
            "current_user": current_user,
            "all_users": all_users,
            "requests": user_requests,
            "active_page": "my_requests"
        }
    )


@router.get("/requests/{request_id}", response_class=HTMLResponse)
def view_request_details(
    request_id: str,
    request: Request,
    submitted: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = RequestService.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    
    # Check ownership or admin
    if current_user.role != "ADMINISTRATOR" and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    all_users = get_all_users(db)

    return templates.TemplateResponse(
        "request_details.html",
        {
            "request": request,
            "current_user": current_user,
            "all_users": all_users,
            "req": req,
            "is_submitted": submitted,
            "active_page": "details"
        }
    )


@router.get("/admin", response_class=HTMLResponse)
def view_admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMINISTRATOR":
        return RedirectResponse(url="/dashboard", status_code=302)

    all_users = get_all_users(db)
    all_requests = RequestService.get_all_requests(db)

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "all_users": all_users,
            "all_requests": all_requests,
            "active_page": "admin"
        }
    )
