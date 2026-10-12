# Defect Log

**Project:** Certificate Request Management System  
**Institution:** Sri Eshwar College of Engineering  
**Assessment:** Software Engineering SAT II — Case 43  

---

## Defect Summary Table

| Defect ID | Description | Severity | Status | Resolution |
| :--- | :--- | :---: | :---: | :--- |
| **DEF-001** | Test runner unable to resolve `app` package path | Low | **Closed** | Created `pytest.ini` with `pythonpath = .` |
| **DEF-002** | Missing `six` module dependency during PlantUML rendering script | Low | **Closed** | Added `six` dependency to virtualenv |
| **DEF-003** | Pydantic V2 class Config deprecation warnings | Low | **Closed** | Migrated schemas to `ConfigDict` |

---

## Detailed Defect Entries

### Defect: DEF-001
- **Defect ID:** DEF-001
- **Description:** Pytest failed to import application modules during initial test collection (`ModuleNotFoundError: No module named 'app'`).
- **Severity:** Low (Tooling Configuration)
- **Reproduction Steps:**
  1. Execute `pytest -v` from project root without setting `PYTHONPATH`.
- **Expected Behavior:** Pytest discovers the current working directory as part of Python search path.
- **Actual Behavior:** Pytest failed to load `tests/conftest.py`.
- **Root Cause:** In Python 3.13 / Pytest 9.1, the working directory is not automatically appended to `sys.path` unless configured in pytest settings.
- **Fix:** Created `pytest.ini` declaring `pythonpath = .` and `testpaths = tests`.
- **Retest Outcome:** Verified. Pytest successfully collected and executed all 12 test modules.

---

### Defect: DEF-002
- **Defect ID:** DEF-002
- **Description:** PlantUML python wrapper threw `ModuleNotFoundError: No module named 'six'`.
- **Severity:** Low (Documentation Build Script)
- **Reproduction Steps:**
  1. Run diagram rendering script: `python -c "import plantuml; ..."`
- **Expected Behavior:** Diagrams render to `docs/use_case.png` and `docs/class_diagram.png`.
- **Actual Behavior:** Script aborted due to missing `six` package required by legacy `plantuml` python client.
- **Root Cause:** The `plantuml` pip package has a runtime dependency on `six` that was not bundled.
- **Fix:** Installed `six>=1.17.0` into the virtual environment.
- **Retest Outcome:** Both `docs/use_case.png` and `docs/class_diagram.png` rendered with HTTP 200 and exit code 0.

---

### Defect: DEF-003
- **Defect ID:** DEF-003
- **Description:** Pydantic models in `app/schemas/schemas.py` generated `PydanticDeprecatedSince20` warnings during test runs.
- **Severity:** Low (Code Hygiene)
- **Reproduction Steps:**
  1. Run `pytest -v`.
  2. Inspect warnings section.
- **Expected Behavior:** Clean test execution with zero deprecation warnings.
- **Actual Behavior:** 4 warnings logged about `class Config: from_attributes = True`.
- **Root Cause:** Legacy Pydantic v1 config style in Pydantic v2 environment.
- **Fix:** Replaced `class Config:` with `model_config = ConfigDict(from_attributes=True)`.
- **Retest Outcome:** Warnings eliminated from application models; verified all schemas work identically.

---

## Final Verification Note
Across all twelve mandatory functional scenarios (T1–T12), **zero runtime functional defects were observed**. All business rules (BR1–BR10) and functional requirements (FR1–FR10) performed strictly according to specifications.
