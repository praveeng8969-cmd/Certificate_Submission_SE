import os
import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.resource import Resource

TEST_DB_FILE = "test_certificate_system.db"
TEST_DATABASE_URL = f"sqlite:///./{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Remove old test DB if present
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    Base.metadata.create_all(bind=test_engine)
    
    # Seed baseline test data
    db = TestingSessionLocal()
    try:
        users = [
            User(id="U001", name="Demo User One", role="USER", status="ACTIVE", phone="9876543210"),
            User(id="U002", name="Demo User Two", role="USER", status="ACTIVE", phone="9876543211"),
            User(id="A001", name="Demo Administrator", role="ADMINISTRATOR", status="ACTIVE", phone="9876543212"),
        ]
        for u in users:
            if not db.query(User).filter(User.id == u.id).first():
                db.add(u)

        resources = [
            Resource(id="S101", service_name="Certificate Request A", capacity=10, status="ACTIVE", base_value=Decimal("500.00"), charge_applicable=True),
            Resource(id="S102", service_name="Certificate Request B", capacity=5, status="ACTIVE", base_value=Decimal("1500.00"), charge_applicable=True),
            Resource(id="S103", service_name="Certificate Request C", capacity=0, status="INACTIVE", base_value=Decimal("0.00"), charge_applicable=False),
        ]
        for r in resources:
            if not db.query(Resource).filter(Resource.id == r.id).first():
                db.add(r)
        
        db.commit()
    finally:
        db.close()

    yield

    # Teardown
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
