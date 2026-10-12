# Test Cases Specification & Traceability

**Project:** Certificate Request Management System  
**Institution:** Sri Eshwar College of Engineering  
**Assessment:** Software Engineering SAT II — Case 43  
**Framework:** Pytest 9.1.1, FastAPI TestClient (Starlette / HTTPX)  

---

## Summary of Test Cases (T1 – T12)

| Test ID | Linked Rules | Test Title / Description | Status |
| :--- | :--- | :--- | :--- |
| **T1** | FR6, BR7 | Submit same request twice (Idempotency) | **PASSED** |
| **T2** | FR5, BR1 | Test active-request counts 4, 5, and attempted 6 | **PASSED** |
| **T3** | FR2, BR2, BR6 | Submit against inactive/ineligible resource | **PASSED** |
| **T4** | FR4, BR4 | Charge calculation boundaries (₹999, ₹1,000, ₹1,001) | **PASSED** |
| **T5** | FR3, FR6, BR7 | Complete valid submission with atomic snapshot & reservation | **PASSED** |
| **T6** | FR5, BR5, BR6 | Submit invalid/missing details (Blank name, invalid phone) | **PASSED** |
| **T7** | FR2, BR2, BR6 | Change resource eligibility/availability before acceptance | **PASSED** |
| **T8** | FR1, FR7, BR10| User cross-access and unauthorized administrative action | **PASSED** |
| **T9** | FR9, FR10, BR8| Administrator valid transitions and stage skipping attempts | **PASSED** |
| **T10**| FR8, BR9 | Cancel submitted request twice & single capacity restoration | **PASSED** |
| **T11**| NFR1, NFR2 | Restart application process after submission & verify disk persistence | **PASSED** |
| **T12**| BR3 | Change resource master data after submission (Snapshot immutability) | **PASSED** |

---

## Detailed Test Case Records

### Test Case: T1
- **Test ID:** T1
- **Linked Requirement / Rule:** FR6, BR7
- **Target File:** `tests/test_submission.py::test_t1_submit_same_request_twice`
- **Input / Precondition:** Same request payload submitted twice with identical `idempotency_key` under `U001` against resource `S101` (initial capacity: 10).
- **Expected Result:** First submission accepted (HTTP 201), capacity decremented to 9. Second submission recognized as duplicate; returns existing request without extra decrement or duplicate database row.
- **Actual Result:** First returned HTTP 201 (`req_id`), resource capacity updated from 10 to 9. Second returned matching `req_id`, capacity remained 9, total rows with key in DB = 1.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T2
- **Test ID:** T2
- **Linked Requirement / Rule:** FR5, BR1
- **Target File:** `tests/test_validation.py::test_t2_active_request_limits_4_5_6`
- **Input / Precondition:** User `U002` submits 4 requests, then attempts a 5th, then attempts a 6th request.
- **Expected Result:** 4th request succeeds (active count 4); 5th request succeeds (active count 5); 6th request rejected with HTTP 400 (`quota exceeded`). Database maintains exactly 5 active records.
- **Actual Result:** Requests 1–5 created with HTTP 201. Request 6 rejected with HTTP 400 and detail `"User quota exceeded: already has 5 active requests (maximum allowed is 5)"`. Active count remained 5.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T3
- **Test ID:** T3
- **Linked Requirement / Rule:** FR2, BR2, BR6
- **Target File:** `tests/test_validation.py::test_t3_submit_against_inactive_resource`
- **Input / Precondition:** User `U001` attempts to submit request against resource `S103` (`status = INACTIVE`, `capacity = 0`).
- **Expected Result:** Submission rejected with HTTP 400; zero state changes made to database.
- **Actual Result:** HTTP 400 returned with message `"Certificate service 'S103' is currently inactive"`. Resource status and capacity remained unchanged.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T4
- **Test ID:** T4
- **Linked Requirement / Rule:** FR4, BR4
- **Target File:** `tests/test_validation.py::test_t4_charge_calculation_boundaries`
- **Input / Precondition:** Fee calculation on chargeable resource `S101` for base values ₹999.00, ₹1,000.00, and ₹1,001.00; and on non-chargeable resource `S103`.
- **Expected Result:** ₹999.00 yields ₹50.00; ₹1,000.00 yields ₹0.00; ₹1,001.00 yields ₹0.00; non-chargeable yields ₹0.00.
- **Actual Result:** Verified exact decimal calculations: `₹999.00 -> ₹50.00`, `₹1,000.00 -> ₹0.00`, `₹1,001.00 -> ₹0.00`, `S103 -> ₹0.00`.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T5
- **Test ID:** T5
- **Linked Requirement / Rule:** FR3, FR6, BR7
- **Target File:** `tests/test_submission.py::test_t5_complete_valid_submission`
- **Input / Precondition:** Valid payload submitted by `U001` with base value ₹800.00 against `S101`.
- **Expected Result:** Request created in status `SUBMITTED`, calculated charge ₹50.00, resource reserved flag set to true, capacity decremented by 1, snapshot persisted, and `request_status_history` inserted atomically.
- **Actual Result:** HTTP 201 received. Database verified: request row inserted, snapshot verified with matching fields, capacity decremented by 1, status history logged `None -> SUBMITTED`.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T6
- **Test ID:** T6
- **Linked Requirement / Rule:** FR5, BR5, BR6
- **Target File:** `tests/test_validation.py::test_t6_submit_invalid_missing_details`
- **Input / Precondition:** Submissions with: (1) blank applicant name, (2) 9-digit phone number.
- **Expected Result:** Rejections with HTTP 400 / 422; no request created; resource capacity unchanged.
- **Actual Result:** Blank name rejected (`"Applicant name cannot be blank or whitespace"`). 9-digit phone rejected (`"Phone number must contain exactly 10 digits"`). Capacity unchanged.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T7
- **Test ID:** T7
- **Linked Requirement / Rule:** FR2, BR2, BR6
- **Target File:** `tests/test_snapshot.py::test_t7_change_resource_eligibility_before_acceptance`
- **Input / Precondition:** Resource `S102` altered to `INACTIVE` immediately prior to request submission acceptance.
- **Expected Result:** Immediate revalidation rejects submission with HTTP 400; no request persisted.
- **Actual Result:** Backend revalidation triggered at transaction time, returned HTTP 400 (`"Certificate service 'S102' is currently inactive"`). No row created.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T8
- **Test ID:** T8
- **Linked Requirement / Rule:** FR1, FR7, BR10
- **Target File:** `tests/test_authorization.py::test_t8_user_cross_access_and_admin_action_forbidden`
- **Input / Precondition:** Request created by `U001`. `U002` attempts to view and cancel it. `U001` attempts to access admin endpoint `/api/admin/requests` and advance status.
- **Expected Result:** All cross-access and non-admin calls rejected with HTTP 403 Forbidden; no state changes made.
- **Actual Result:** Viewing non-owned request returned 403; cancelling non-owned request returned 403; admin queue and stage advance returned 403. Request remained `SUBMITTED`.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T9
- **Test ID:** T9
- **Linked Requirement / Rule:** FR9, FR10, BR8
- **Target File:** `tests/test_status.py::test_t9_admin_valid_transitions_and_stage_skipping`
- **Input / Precondition:** Admin attempts: (1) stage skip `SUBMITTED -> IN_PROGRESS`, (2) valid sequence `SUBMITTED -> APPROVED -> IN_PROGRESS -> COMPLETED`, (3) reopening `COMPLETED -> APPROVED`.
- **Expected Result:** Skipping and reopening rejected with HTTP 400; sequential progression succeeds at each step.
- **Actual Result:** Direct leap to `IN_PROGRESS` rejected with HTTP 400 (`"Stage skipping or reopening terminal states is prohibited"`). Valid steps transitioned correctly: `APPROVED` -> `IN_PROGRESS` -> `COMPLETED`. Reopening rejected with HTTP 400.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T10
- **Test ID:** T10
- **Linked Requirement / Rule:** FR8, BR9
- **Target File:** `tests/test_status.py::test_t10_cancel_submitted_request_twice`
- **Input / Precondition:** Request in `SUBMITTED` cancelled by owner, then cancelled a second time.
- **Expected Result:** First cancellation updates status to `CANCELLED` and restores 1 capacity unit. Second cancellation rejected with HTTP 400 without double-restoring capacity.
- **Actual Result:** First call returned HTTP 200, status `CANCELLED`, `resource_released=True`, capacity restored from 9 to 10. Second call returned HTTP 400 (`"Request has already been cancelled"`), capacity remained 10.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T11
- **Test ID:** T11
- **Linked Requirement / Rule:** NFR1, NFR2
- **Target File:** `tests/test_persistence.py::test_t11_restart_application_persistence`
- **Input / Precondition:** Process 1 initializes DB file, submits request, updates capacity to 9, and terminates. Process 2 spawns as fresh OS process, connects to database file, and queries records.
- **Expected Result:** Process 2 retrieves request with status `SUBMITTED` and verified capacity 9 from SQLite disk storage.
- **Actual Result:** Process 1 exited with code 0. Process 2 spawned, retrieved request ID, verified status `SUBMITTED` and resource capacity 9 (`PERSISTENCE_VERIFIED:SUBMITTED:9`).
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`

---

### Test Case: T12
- **Test ID:** T12
- **Linked Requirement / Rule:** BR3
- **Target File:** `tests/test_snapshot.py::test_t12_change_resource_master_data_after_submission`
- **Input / Precondition:** Request submitted with initial resource master data (`Certificate Request A`, charge ₹50.00). Resource master row subsequently altered (`service_name = "MODIFIED MASTER SERVICE NAME"`, `base_value = 9999.00`, `charge_applicable = False`).
- **Expected Result:** Request's historical snapshot remains completely unmodified and reflects original submission parameters.
- **Actual Result:** Historical snapshot queried via API retained original name `"Certificate Request A"` and fee `"50.00"`.
- **Verdict:** **PASS**
- **Evidence:** `docs/evidence/test_run.log`
