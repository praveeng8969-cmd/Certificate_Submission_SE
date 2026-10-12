import uuid
from app.models.request import ServiceRequest


def test_t8_user_cross_access_and_admin_action_forbidden(client, db_session):
    """
    T8: User accesses another user's request or administrator action.
    Expected: Access denied (403); no state changes (BR10).
    """
    # 1. Create a request owned by U001
    payload = {
        "resource_id": "S101",
        "name": "User One Special Request",
        "phone": "9876543210",
        "description": "Owner only access",
        "reference": "REF-AUTH-001",
        "base_value": 300.00,
        "idempotency_key": f"IDEM-AUTH-{uuid.uuid4().hex}"
    }
    resp_create = client.post("/api/requests/submit", json=payload, headers={"X-User-Id": "U001"})
    assert resp_create.status_code == 201
    req_id = resp_create.json()["id"]

    # 2. User U002 tries to view U001's request -> 403 Forbidden
    resp_view = client.get(f"/api/requests/{req_id}", headers={"X-User-Id": "U002"})
    assert resp_view.status_code == 403

    # 3. User U002 tries to cancel U001's request -> 403 Forbidden
    resp_cancel = client.post(f"/api/requests/{req_id}/cancel", headers={"X-User-Id": "U002"})
    assert resp_cancel.status_code == 403

    # 4. User U001 tries to perform Administrator action (list all requests) -> 403 Forbidden
    resp_admin_list = client.get("/api/admin/requests", headers={"X-User-Id": "U001"})
    assert resp_admin_list.status_code == 403

    # 5. User U001 tries to advance request status -> 403 Forbidden
    resp_admin_advance = client.post(
        f"/api/admin/requests/{req_id}/advance",
        json={"target_status": "APPROVED"},
        headers={"X-User-Id": "U001"}
    )
    assert resp_admin_advance.status_code == 403

    # Verify request status remains SUBMITTED without changes
    db_session.expire_all()
    req = db_session.query(ServiceRequest).filter(ServiceRequest.id == req_id).first()
    assert req.status == "SUBMITTED"
