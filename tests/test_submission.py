import uuid
from decimal import Decimal
from app.models.resource import Resource
from app.models.request import ServiceRequest
from app.models.history import RequestStatusHistory


def test_t1_submit_same_request_twice(client, db_session):
    """
    T1: Submit same request twice (Idempotency).
    Expected: No duplicate accepted request or extra resource reservation.
    """
    idempotency_key = f"IDEM-TEST-T1-{uuid.uuid4().hex}"
    resource_id = "S101"

    # Get initial capacity
    res = db_session.query(Resource).filter(Resource.id == resource_id).first()
    initial_capacity = res.capacity

    payload = {
        "resource_id": resource_id,
        "name": "Demo User One",
        "phone": "9876543210",
        "description": "Idempotency test description",
        "reference": "REF-T1-001",
        "base_value": 450.00,
        "idempotency_key": idempotency_key
    }

    headers = {"X-User-Id": "U001"}

    # First submission
    response_1 = client.post("/api/requests/submit", json=payload, headers=headers)
    assert response_1.status_code == 201
    data_1 = response_1.json()
    req_id_1 = data_1["id"]

    # Capacity after first submission must decrease by exactly 1
    db_session.expire_all()
    res_after_1 = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after_1.capacity == initial_capacity - 1

    # Second submission with same idempotency key
    response_2 = client.post("/api/requests/submit", json=payload, headers=headers)
    assert response_2.status_code in [200, 201]
    data_2 = response_2.json()

    # Must return the same request ID
    assert data_2["id"] == req_id_1

    # Capacity must NOT be decremented a second time
    db_session.expire_all()
    res_after_2 = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after_2.capacity == initial_capacity - 1

    # Database must contain exactly one request for this idempotency key
    req_count = db_session.query(ServiceRequest).filter(
        ServiceRequest.idempotency_key == idempotency_key
    ).count()
    assert req_count == 1


def test_t5_complete_valid_submission(client, db_session):
    """
    T5: Complete valid submission.
    Expected: Request, snapshot, reservation, and history saved atomically.
    """
    idempotency_key = f"IDEM-TEST-T5-{uuid.uuid4().hex}"
    resource_id = "S101"

    db_session.expire_all()
    res = db_session.query(Resource).filter(Resource.id == resource_id).first()
    initial_cap = res.capacity

    payload = {
        "resource_id": resource_id,
        "name": "Jane Doe",
        "phone": "9123456789",
        "description": "Graduation Certificate requirement",
        "reference": "REF-GRAD-2026",
        "base_value": 800.00,
        "idempotency_key": idempotency_key
    }

    headers = {"X-User-Id": "U001"}
    response = client.post("/api/requests/submit", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    req_id = data["id"]
    assert data["status"] == "SUBMITTED"
    assert Decimal(str(data["service_charge"])) == Decimal("50.00")
    assert data["resource_reserved"] is True
    assert data["resource_released"] is False

    # Verify atomic snapshot
    snapshot = data["snapshot_data"]
    assert snapshot["applicant_name"] == "Jane Doe"
    assert snapshot["phone"] == "9123456789"
    assert snapshot["resource_id"] == "S101"
    assert snapshot["service_charge"] == "50.00"

    # Verify resource capacity decremented by 1
    db_session.expire_all()
    res_after = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after.capacity == initial_cap - 1

    # Verify status history saved
    histories = db_session.query(RequestStatusHistory).filter(
        RequestStatusHistory.reference_id == req_id
    ).all()
    assert len(histories) == 1
    assert histories[0].old_status is None
    assert histories[0].new_status == "SUBMITTED"
    assert histories[0].actor_id == "U001"
