from app.routers.auth import router as auth_router
from app.routers.requests import router as requests_router
from app.routers.admin import router as admin_router

__all__ = ["auth_router", "requests_router", "admin_router"]
