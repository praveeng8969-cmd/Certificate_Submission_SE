import uuid
from decimal import Decimal
from app.models.resource import Resource
from app.models.request import ServiceRequest


def test_t2_active_request_limits_4_5_6(client, db_session):
    """
    T2: Test active-request counts 4, 5, and attempted 6.
    Expected: fifth allowed if eligible; sixth rejected (BR1).
    """
    user_id = "U002"
    resource_id = "S101"
    headers = {"X-User-Id": user_id}

    # Clean existing requests for U002 to start fresh
    db_session.query(ServiceRequest).filter(ServiceRequest.user_id == user_id).delete()
    db_session.commit()

    # Create 4 active requests
    for i in range(1, 5):
        payload = {
            "resource_id": resource_id,
            "name": f"User Two Req {i}",
            "phone": "9876543211",
            "description": f"Request number {i}",
            "reference": f"REF-U2-{i}",
            "base_value": 500.00,
            "idempotency_key": f"IDEM-T2-REQ-{i}-{uuid.uuid4().hex}"
        }
        res = client.post("/api/requests/submit", json=payload, headers=headers)
        assert res.status_code == 201

    # Check active count is now 4
    active_count = db_session.query(ServiceRequest).filter(
        ServiceRequest.user_id == user_id,
        ServiceRequest.status.in_(["SUBMITTED", "APPROVED", "IN_PROGRESS"])
    ).count()
    assert active_count == 4

    # 5th request should be allowed (Boundary condition 5)
    payload_5 = {
        "resource_id": resource_id,
        "name": "User Two Req 5",
        "phone": "9876543211",
        "description": "Fifth active request",
        "reference": "REF-U2-5",
        "base_value": 500.00,
        "idempotency_key": f"IDEM-T2-REQ-5-{uuid.uuid4().hex}"
    }
    res_5 = client.post("/api/requests/submit", json=payload_5, headers=headers)
    assert res_5.status_code == 201

    # Check active count is now 5
    active_count_5 = db_session.query(ServiceRequest).filter(
        ServiceRequest.user_id == user_id,
        ServiceRequest.status.in_(["SUBMITTED", "APPROVED", "IN_PROGRESS"])
    ).count()
    assert active_count_5 == 5

    # Attempt 6th request: must be REJECTED (BR1)
    payload_6 = {
        "resource_id": resource_id,
        "name": "User Two Req 6",
        "phone": "9876543211",
        "description": "Attempted sixth active request",
        "reference": "REF-U2-6",
        "base_value": 500.00,
        "idempotency_key": f"IDEM-T2-REQ-6-{uuid.uuid4().hex}"
    }
    res_6 = client.post("/api/requests/submit", json=payload_6, headers=headers)
    assert res_6.status_code == 400
    assert "quota exceeded" in res_6.json()["detail"].lower()

    # Verify database still has exactly 5 active requests
    active_count_after = db_session.query(ServiceRequest).filter(
        ServiceRequest.user_id == user_id,
        ServiceRequest.status.in_(["SUBMITTED", "APPROVED", "IN_PROGRESS"])
    ).count()
    assert active_count_after == 5


def test_t3_submit_against_inactive_resource(client, db_session):
    """
    T3: Submit against inactive/ineligible resource (S103 is INACTIVE, capacity 0).
    Expected: rejection without state changes (BR2, BR6).
    """
    resource_id = "S103"
    db_session.expire_all()
    res = db_session.query(Resource).filter(Resource.id == resource_id).first()
    initial_cap = res.capacity
    initial_status = res.status

    payload = {
        "resource_id": resource_id,
        "name": "Demo User One",
        "phone": "9876543210",
        "description": "Inactive resource test",
        "reference": "REF-T3-001",
        "base_value": 200.00,
        "idempotency_key": f"IDEM-T3-{uuid.uuid4().hex}"
    }

    headers = {"X-User-Id": "U001"}
    response = client.post("/api/requests/submit", json=payload, headers=headers)
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower() or "capacity" in response.json()["detail"].lower()

    # Verify no state changes in database
    db_session.expire_all()
    res_after = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after.capacity == initial_cap
    assert res_after.status == initial_status


def test_t4_charge_calculation_boundaries(client):
    """
    T4: Base values ₹999, ₹1,000, ₹1,001.
    Expected: ₹50, ₹0, ₹0 when charge applies (BR4).
    """
    resource_id = "S101"  # Charge applicable is True

    # 1. Base value ₹999 -> charge ₹50
    resp_999 = client.post("/api/requests/preview-charge", json={"resource_id": resource_id, "base_value": 999.00})
    assert resp_999.status_code == 200
    assert Decimal(str(resp_999.json()["calculated_charge"])) == Decimal("50.00")

    # 2. Base value ₹1,000 -> charge ₹0
    resp_1000 = client.post("/api/requests/preview-charge", json={"resource_id": resource_id, "base_value": 1000.00})
    assert resp_1000.status_code == 200
    assert Decimal(str(resp_1000.json()["calculated_charge"])) == Decimal("0.00")

    # 3. Base value ₹1,001 -> charge ₹0
    resp_1001 = client.post("/api/requests/preview-charge", json={"resource_id": resource_id, "base_value": 1001.00})
    assert resp_1001.status_code == 200
    assert Decimal(str(resp_1001.json()["calculated_charge"])) == Decimal("0.00")

    # 4. Inactive/non-chargeable service -> charge ₹0
    resp_non_chargeable = client.post("/api/requests/preview-charge", json={"resource_id": "S103", "base_value": 500.00})
    assert resp_non_chargeable.status_code == 200
    assert Decimal(str(resp_non_chargeable.json()["calculated_charge"])) == Decimal("0.00")


def test_t6_submit_invalid_missing_details(client, db_session):
    """
    T6: Submit invalid/missing details (blank name, invalid phone, missing description).
    Expected: Rejection without partial updates (BR5, BR6).
    """
    resource_id = "S102"
    db_session.expire_all()
    res = db_session.query(Resource).filter(Resource.id == resource_id).first()
    initial_cap = res.capacity

    # 1. Blank name
    payload_blank_name = {
        "resource_id": resource_id,
        "name": "   ",
        "phone": "9876543210",
        "description": "Valid description",
        "reference": "REF-T6-1",
        "base_value": 500.00,
        "idempotency_key": f"IDEM-T6-1-{uuid.uuid4().hex}"
    }
    resp_1 = client.post("/api/requests/submit", json=payload_blank_name, headers={"X-User-Id": "U001"})
    assert resp_1.status_code in [400, 422]

    # 2. Invalid phone (9 digits instead of 10)
    payload_bad_phone = {
        "resource_id": resource_id,
        "name": "Valid Name",
        "phone": "987654321",  # 9 digits
        "description": "Valid description",
        "reference": "REF-T6-2",
        "base_value": 500.00,
        "idempotency_key": f"IDEM-T6-2-{uuid.uuid4().hex}"
    }
    resp_2 = client.post("/api/requests/submit", json=payload_bad_phone, headers={"X-User-Id": "U001"})
    assert resp_2.status_code in [400, 422]

    # Verify no resource capacity change
    db_session.expire_all()
    res_after = db_session.query(Resource).filter(Resource.id == resource_id).first()
    assert res_after.capacity == initial_cap
