# AI-Assisted Test & Engineering Report

**Project Name:** Certificate Request Management System  
**Institution:** Sri Eshwar College of Engineering  
**Assessment:** Software Engineering SAT II — Case 43  
**Environment:** Windows 10/11 x64, SQLite 3  
**Python Version:** Python 3.13.14  
**Primary Dependencies:**
- `fastapi` == 0.143.0
- `sqlalchemy` == 2.1.4
- `pydantic` == 2.14.1
- `pytest` == 9.1.1
- `jinja2` == 3.1.6
- `httpx` == 0.28.1
- `starlette` == 1.7.0
**Git Commit Hash:** `ea44f2565ad3bbbd8499fa73f9e171ffc6850d5d`

---

## 1. Test Execution Metrics

| Metric | Result |
| :--- | :--- |
| **Total Test Scenarios Executed** | 12 |
| **Passed Count** | 12 |
| **Failed Count** | 0 |
| **Not-Run / Skipped Count** | 0 |
| **Overall Pass Percentage** | **100%** |

---

## 2. Representative AI Interactions & Student Review

### 2.1 Representative AI Prompt
> *"Generate the atomic database transaction logic for request creation and resource reservation in `app/services/request_service.py`, handling idempotency duplicate retry vs fresh submission and negative capacity prevention."*

### 2.2 AI-Generated Suggestion
The AI originally proposed checking the idempotency key and capacity using two separate select statements, then performing standard ORM updates:
```python
existing = db.query(ServiceRequest).filter_by(idempotency_key=key).first()
if existing:
    return existing
resource = db.query(Resource).filter_by(id=res_id).first()
resource.capacity -= 1
db.commit()
```

### 2.3 Student / Peer Engineering Review
During code review, the student observed two architectural vulnerabilities in the initial suggestion:
1. Under high concurrent load, two simultaneous requests could read the same available capacity $> 0$ and both decrement it, leading to race conditions and negative capacity.
2. In Pydantic V2, legacy `class Config: from_attributes = True` emits deprecation warnings that should be migrated to `model_config = ConfigDict(from_attributes=True)`.
3. In Pytest, running from the repository root required explicit module path resolution via `pytest.ini`.

### 2.4 Accepted and Corrected Implementation
1. Enforced atomic SQL-level conditional updates:
   ```python
   stmt = (
       update(Resource)
       .where(Resource.id == resource.id, Resource.capacity > 0)
       .values(capacity=Resource.capacity - 1, updated_at=datetime.now(timezone.utc))
   )
   result = db.execute(stmt)
   if result.rowcount == 0:
       raise HTTPException(status_code=409, detail="Capacity exhausted")
   ```
2. Refactored all Pydantic schemas to utilize modern `model_config = ConfigDict(from_attributes=True)`.
3. Created `pytest.ini` with `pythonpath = .` ensuring zero-configuration execution.

---

## 3. Defect Analysis & Retest Results

- **Observed In-Development Defects:**
  - *Module import resolution in Pytest:* Initially triggered `ModuleNotFoundError: No module named 'app'`. Resolved by configuring `pytest.ini`. Retested: Passed.
  - *PlantUML library dependency:* Initial PNG generation required python `six` package for the wrapper. Resolved by installing `six`. Retested: Both PNG diagrams rendered cleanly.
- **Automated Test Suite Execution:** Zero runtime defects detected across all 12 mandatory test cases (T1–T12).
- **Retest Outcome:** Full suite re-run confirmed 12 of 12 tests passed without failures.

---

## 4. Known Limitations

1. **Simulated Authentication:** Production OAuth2 / JWT / SSO authentication is abstracted with a role switcher and simulated session cookie (`session_user_id`) in accordance with the project scope.
2. **SQLite Database Concurrency:** SQLite utilizes table-level locking during writes. For large-scale distributed deployments exceeding 1,000 write operations per second, PostgreSQL with row-level locking (`SELECT ... FOR UPDATE`) is recommended.

---

## 5. Future Improvements

1. Integration with institutional LDAP / Single Sign-On (SSO) systems.
2. Automated PDF certificate generation and digital signing (PKI / X.509 certificates).
3. Email and SMS notification webhooks for status transition updates.
