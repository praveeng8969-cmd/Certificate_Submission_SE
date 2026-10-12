import os
import sys
import subprocess
import json

PERSISTENCE_DB = "persistence_test_store.db"


def test_t11_restart_application_persistence():
    """
    T11: Restart application after submission.
    Expected: Request and changed resource state remain persisted.
    Strict Requirement: Must include a real process restart and database persistence check,
    not merely creating a new database session.
    """
    if os.path.exists(PERSISTENCE_DB):
        try:
            os.remove(PERSISTENCE_DB)
        except Exception:
            pass

    # Script 1: Run in Process 1 - initialize DB, seed, and submit a request
    script_process_1 = f"""
import os, sys
from decimal import Decimal
os.environ["DATABASE_URL"] = "sqlite:///./{PERSISTENCE_DB}"

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.resource import Resource
from app.schemas.schemas import RequestCreateSchema
from app.services.request_service import RequestService

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Seed baseline
u = User(id="U001", name="Persistent User", role="USER", status="ACTIVE", phone="9876543210")
r = Resource(id="S101", service_name="Certificate Request A", capacity=10, status="ACTIVE", base_value=Decimal("500.00"), charge_applicable=True)
db.add(u)
db.add(r)
db.commit()

# Submit request
payload = RequestCreateSchema(
    resource_id="S101",
    name="Persistent Applicant",
    phone="9876543210",
    description="Testing across real process termination",
    reference="REF-PERSIST-101",
    base_value=Decimal("500.00"),
    idempotency_key="IDEM-PERSIST-TOKEN-999"
)

req, is_dup = RequestService.create_request(db, "U001", payload, payload.idempotency_key)
print("REQUEST_ID:" + req.id)
db.close()
sys.exit(0)
"""

    result_p1 = subprocess.run(
        [sys.executable, "-c", script_process_1],
        capture_output=True,
        text=True
    )
    assert result_p1.returncode == 0, f"Process 1 failed with error: {result_p1.stderr}"
    
    # Extract request ID created in Process 1
    req_id = None
    for line in result_p1.stdout.splitlines():
        if line.startswith("REQUEST_ID:"):
            req_id = line.split("REQUEST_ID:")[1].strip()
    assert req_id is not None

    # Process 1 has fully terminated. Now launch Process 2 (simulating application restart)
    script_process_2 = f"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:///./{PERSISTENCE_DB}"

from app.database import engine, SessionLocal
from app.models.resource import Resource
from app.models.request import ServiceRequest

db = SessionLocal()
req = db.query(ServiceRequest).filter(ServiceRequest.id == "{req_id}").first()
res = db.query(Resource).filter(Resource.id == "S101").first()

if not req:
    print("ERROR: Request not found")
    sys.exit(1)

if res.capacity != 9:
    print(f"ERROR: Expected capacity 9, got {{res.capacity}}")
    sys.exit(2)

print("PERSISTENCE_VERIFIED:" + req.status + ":" + str(res.capacity))
db.close()
sys.exit(0)
"""

    result_p2 = subprocess.run(
        [sys.executable, "-c", script_process_2],
        capture_output=True,
        text=True
    )
    assert result_p2.returncode == 0, f"Process 2 failed with error: {result_p2.stderr}"
    assert "PERSISTENCE_VERIFIED:SUBMITTED:9" in result_p2.stdout

    # Clean up persistence test DB file
    if os.path.exists(PERSISTENCE_DB):
        try:
            os.remove(PERSISTENCE_DB)
        except Exception:
            pass
