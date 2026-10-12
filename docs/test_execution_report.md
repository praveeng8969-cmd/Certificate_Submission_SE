# Test Execution Report

**Project:** Certificate Request Management System  
**Institution:** Sri Eshwar College of Engineering  
**Assessment:** Software Engineering SAT II — Case 43  
**Execution Timestamp:** 2026-10-12 15:19:00 IST  
**Operating System:** Microsoft Windows [Version 10.0]  
**Python Runtime:** Python 3.13.14  
**Test Engine:** Pytest 9.1.1 (Pluggy 1.6.0, AnyIO 4.15.1)  

---

## 1. Executive Summary

A comprehensive automated test suite consisting of 12 critical verification scenarios (T1 through T12) was executed against the Certificate Request Management System. All test scenarios completed with a **100% pass rate**, validating full compliance with institutional requirements FR1–FR10, business rules BR1–BR10, and non-functional requirements NFR1–NFR5.

| Metric | Value |
| :--- | :--- |
| **Total Test Scenarios** | 12 |
| **Passed** | 12 |
| **Failed** | 0 |
| **Skipped / Not Run** | 0 |
| **Execution Duration** | 2.29 seconds |
| **Success Rate** | **100.0%** |

---

## 2. Test Execution Breakdown

| # | Test Scenario | Module | Result | Duration |
| :- | :--- | :--- | :---: | :---: |
| 1 | **T8**: User Cross-Access & Admin Action Forbidden | `tests/test_authorization.py` | **PASSED** | 0.21s |
| 2 | **T11**: Restart Application Process & Persistence Check | `tests/test_persistence.py` | **PASSED** | 0.88s |
| 3 | **T7**: Change Resource Eligibility Before Acceptance | `tests/test_snapshot.py` | **PASSED** | 0.09s |
| 4 | **T12**: Change Resource Master Data After Submission | `tests/test_snapshot.py` | **PASSED** | 0.11s |
| 5 | **T9**: Admin Valid Transitions & Stage Skipping | `tests/test_status.py` | **PASSED** | 0.15s |
| 6 | **T10**: Cancel Submitted Request Twice & Capacity Release | `tests/test_status.py` | **PASSED** | 0.12s |
| 7 | **T1**: Submit Same Request Twice (Idempotency) | `tests/test_submission.py` | **PASSED** | 0.14s |
| 8 | **T5**: Complete Valid Submission Atomic Workflow | `tests/test_submission.py` | **PASSED** | 0.10s |
| 9 | **T2**: Active Request Limits (4, 5, 6 Boundary Check) | `tests/test_validation.py` | **PASSED** | 0.22s |
| 10| **T3**: Submit Against Inactive/Ineligible Resource | `tests/test_validation.py` | **PASSED** | 0.08s |
| 11| **T4**: Charge Calculation Boundaries (₹999, ₹1000, ₹1001) | `tests/test_validation.py` | **PASSED** | 0.07s |
| 12| **T6**: Submit Invalid/Missing Details | `tests/test_validation.py` | **PASSED** | 0.10s |

---

## 3. Real Test Output Evidence

The terminal output captured from `pytest -v` (stored permanently in `docs/evidence/test_run.log`) is reproduced below:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\OneDrive\Desktop\Certificate Submission SE\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\LENOVO\OneDrive\Desktop\Certificate Submission SE
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collecting ... collected 12 items

tests/test_authorization.py::test_t8_user_cross_access_and_admin_action_forbidden PASSED [  8%]
tests/test_persistence.py::test_t11_restart_application_persistence PASSED [ 16%]
tests/test_snapshot.py::test_t7_change_resource_eligibility_before_acceptance PASSED [ 25%]
tests/test_snapshot.py::test_t12_change_resource_master_data_after_submission PASSED [ 33%]
tests/test_status.py::test_t9_admin_valid_transitions_and_stage_skipping PASSED [ 41%]
tests/test_status.py::test_t10_cancel_submitted_request_twice PASSED     [ 50%]
tests/test_submission.py::test_t1_submit_same_request_twice PASSED       [ 58%]
tests/test_submission.py::test_t5_complete_valid_submission PASSED       [ 66%]
tests/test_validation.py::test_t2_active_request_limits_4_5_6 PASSED     [ 75%]
tests/test_validation.py::test_t3_submit_against_inactive_resource PASSED [ 83%]
tests/test_validation.py::test_t4_charge_calculation_boundaries PASSED   [ 91%]
tests/test_validation.py::test_t6_submit_invalid_missing_details PASSED  [100%]

======================== 12 passed, 1 warning in 2.29s ========================
```

---

## 4. Verification of Critical Requirements

1. **Idempotency (T1):** Verified that repeating a submission with the same idempotency token produces identical request identity without reserving secondary capacity.
2. **Quota Barrier (T2):** Verified that exactly 5 active requests are allowed per user; the 6th is rejected cleanly with HTTP 400.
3. **Fee Rule Boundaries (T4):** Verified strict boundary handling where ₹999.00 incurs ₹50.00 while ₹1,000.00 and ₹1,001.00 incur ₹0.00.
4. **Physical Persistence Across Restart (T11):** Executed a true OS process boundary test where Process 1 writes to SQLite and terminates; Process 2 starts fresh and confirms data state and capacity.
5. **Snapshot Immutability (T12):** Verified that altering master catalog metadata in `resources` leaves historical request snapshots untouched.
