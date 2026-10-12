from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base, SessionLocal
from app.routers.auth import router as auth_router
from app.routers.requests import router as requests_router
from app.routers.admin import router as admin_router
from app.routers.views import router as views_router
from scripts.seed_data import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed baseline data on startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db_session=db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Certificate Request Management System",
    description="SE SAT II Academic Assessment - Case 43: Certificate Request System",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static assets
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API and View Routers
app.include_router(auth_router)
app.include_router(requests_router)
app.include_router(admin_router)
app.include_router(views_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
