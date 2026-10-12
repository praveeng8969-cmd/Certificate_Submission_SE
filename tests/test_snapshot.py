import uuid
from decimal import Decimal
from app.models.resource import Resource
from app.models.request import ServiceRequest


def test_t7_change_resource_eligibility_before_acceptance(client, db_session):
    """
    T7: Change resource eligibility/availability before acceptance.
    Expected: Revalidation and rejection without partial updates (BR2, BR6).
    """
    resource_id = "S102"
    
    # Simulate resource becoming inactive right before submission is processed
    res = db_session.query(Resource).filter(Resource.id == resource_id).first()
    res.status = "INACTIVE"
    db_session.commit()

    payload = {
        "resource_id": resource_id,
        "name": "Applicant T7",
        "phone": "9876543210",
        "description": "Eligibility change before acceptance test",
        "reference": "REF-T7-001",
        "base_value": 400.00,
        "idempotency_key": f"IDEM-T7-{uuid.uuid4().hex}"
    }

    resp = client.post("/api/requests/submit", json=payload, headers={"X-User-Id": "U001"})
    assert resp.status_code == 400
    assert "inactive" in resp.json()["detail"].lower()

    # Revert resource status back to ACTIVE for subsequent tests
    res.status = "ACTIVE"
    db_session.commit()


def test_t12_change_resource_master_data_after_submission(client, db_session):
    """
    T12: Change resource master data after submission.
    Expected: Saved historical snapshot remains unchanged (BR3).
    """
    resource_id = "S101"
    
    # 1. Submit request with original master data (Certificate Request A, base_value=500.00, charge=50.00)
    payload = {
        "resource_id": resource_id,
        "name": "Historical Audit Applicant",
        "phone": "9876543210",
        "description": "Snapshot immutability test",
        "reference": "REF-HIST-001",
        "base_value": 500.00,
        "idempotency_key": f"IDEM-HIST-{uuid.uuid4().hex}"
    }

    resp_submit = client.post("/api/requests/submit", json=payload, headers={"X-User-Id": "U001"})
    assert resp_submit.status_code == 201
    data = resp_submit.json()
    req_id = data["id"]
    original_snapshot = data["snapshot_data"]

    assert original_snapshot["resource_service_name"] == "Certificate Request A"
    assert original_snapshot["service_charge"] == "50.00"

    # 2. Modify resource master data in the database
    res = db_session.query(Resource).filter(Resource.id == resource_id).first()
    original_service_name = res.service_name
    original_base = res.base_value

    res.service_name = "MODIFIED MASTER SERVICE NAME"
    res.base_value = Decimal("9999.00")
    res.charge_applicable = False
    db_session.commit()

    # 3. Retrieve request from API
    resp_get = client.get(f"/api/requests/{req_id}", headers={"X-User-Id": "U001"})
    assert resp_get.status_code == 200
    retrieved_data = resp_get.json()

    # Verify that the saved historical snapshot remains UNCHANGED
    saved_snapshot = retrieved_data["snapshot_data"]
    assert saved_snapshot["resource_service_name"] == "Certificate Request A"
    assert saved_snapshot["service_charge"] == "50.00"
    assert saved_snapshot["applicant_name"] == "Historical Audit Applicant"

    # Restore resource master data
    res.service_name = original_service_name
    res.base_value = original_base
    res.charge_applicable = True
    db_session.commit()
