import uuid
from app.models.resource import Resource
from app.models.request import ServiceRequest


def test_t9_admin_valid_transitions_and_stage_skipping(client, db_session):
    """
    T9: Administrator performs valid transitions and attempts stage skipping.
    Expected: Valid sequence succeeds; invalid transition rejected (BR8).
    """
    # Create request by U001
    payload = {
        "resource_id": "S101",
        "name": "Transition Test User",
        "phone": "9876543210",
        "description": "Lifecycle transition test",
        "reference": "REF-TRANS-001",
        "base_value": 750.00,
        "idempotency_key": f"IDEM-TRANS-{uuid.uuid4().hex}"
    }
    resp_create = client.post("/api/requests/submit", json=payload, headers={"X-User-Id": "U001"})
    assert resp_create.status_code == 201
    req_id = resp_create.json()["id"]

    admin_headers = {"X-User-Id": "A001"}

    # Attempt stage skipping: SUBMITTED -> IN_PROGRESS (Skipping APPROVED) -> MUST FAIL (400)
    resp_skip = client.post(
        f"/api/admin/requests/{req_id}/advance",
        json={"target_status": "IN_PROGRESS"},
        headers=admin_headers
    )
    assert resp_skip.status_code == 400
    assert "stage skipping" in resp_skip.json()["detail"].lower() or "invalid transition" in resp_skip.json()["detail"].lower()

    # Attempt stage skipping: SUBMITTED -> COMPLETED -> MUST FAIL (400)
    resp_skip_comp = client.post(
        f"/api/admin/requests/{req_id}/advance",
        json={"target_status": "COMPLETED"},
        headers=admin_headers
    )
    assert resp_skip_comp.status_code == 400

    # Valid step 1: SUBMITTED -> APPROVED -> MUST SUCCEED
    resp_appr = client.post(
        f"/api/admin/requests/{req_id}/advance",
        json={"target_status": "APPROVED"},
        headers=admin_headers
    )
    assert resp_appr.status_code == 200
    assert resp_appr.json()["status"] == "APPROVED"

    # Valid step 2: APPROVED -> IN_PROGRESS -> MUST SUCCEED
    resp_prog = client.post(
        f"/api/admin/requests/{req_id}/advance",
        json={"target_status": "IN_PROGRESS"},
        headers=admin_headers
    )
    assert resp_prog.status_code == 200
    assert resp_prog.json()["status"] == "IN_PROGRESS"

    # Valid step 3: IN_PROGRESS -> COMPLETED -> MUST SUCCEED
    resp_comp = client.post(
        f"/api/admin/requests/{req_id}/advance",
        json={"target_status": "COMPLETED"},
        headers=admin_headers
    )
    assert resp_comp.status_code == 200
    assert resp_comp.json()["status"] == "COMPLETED"

    # Attempt transition from COMPLETED -> APPROVED (reopening) -> MUST FAIL
    resp_reopen = client.post(
        f"/api/admin/requests/{req_id}/advance",
        json={"target_status": "APPROVED"},
        headers=admin_headers
    )
    assert resp_reopen.status_code == 400


def test_t10_cancel_submitted_request_twice(client, db_session):
    """
    T10: Cancel submitted request twice.
    Expected: First cancellation releases capacity once; second rejected without additional effects (BR9).
    """
    resource_id = "S101"
    db_session.expire_all()
    res = db_session.query(Resource).filter(Resource.id == resource_id).first()
    initial_cap = res.capacity

    payload = {
        "resource_id": resource_id,
        "name": "Cancel Test User",
        "phone": "9876543210",
        "description": "Cancellation double test",
        "reference": "REF-CANCEL-001",
        "base_value": 300.00,
        "idempotency_key": f"IDEM-CANCEL-{uuid.uuid4().hex}"
    }

    user_headers = {"X-User-Id": "U001"}
    resp_create = client.post("/api/requests/submit", json=payload, headers=user_headers)
    assert resp_create.status_code == 201
    req_id = resp_create.json()["id"]

    # Capacity decreased by 1
    db_session.expire_all()
    res_after_submit = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after_submit.capacity == initial_cap - 1

    # First Cancellation: MUST SUCCEED and restore 1 capacity unit
    resp_cancel_1 = client.post(f"/api/requests/{req_id}/cancel", headers=user_headers)
    assert resp_cancel_1.status_code == 200
    assert resp_cancel_1.json()["status"] == "CANCELLED"
    assert resp_cancel_1.json()["resource_released"] is True

    # Capacity restored to initial_cap
    db_session.expire_all()
    res_after_cancel_1 = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after_cancel_1.capacity == initial_cap

    # Second Cancellation: MUST BE REJECTED (400)
    resp_cancel_2 = client.post(f"/api/requests/{req_id}/cancel", headers=user_headers)
    assert resp_cancel_2.status_code == 400
    assert "already been cancelled" in resp_cancel_2.json()["detail"].lower()

    # Capacity must NOT be incremented a second time
    db_session.expire_all()
    res_after_cancel_2 = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after_cancel_2.capacity == initial_cap
