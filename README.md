# Certificate Request Management System

**Institution:** Sri Eshwar College of Engineering  
**Course:** Software Engineering  
**Assessment:** Software Engineering SAT II  
**Industry Use Case:** 43 — Certificate Request System  
**Academic Year:** 2025–2026  

---

## 1. Project Overview

The **Certificate Request Management System** is a full-stack, enterprise-grade academic web application designed to manage the end-to-end lifecycle of institutional certificate applications (e.g., Bonafide, Transcript, Degree Verification, Conduct Certificates).

The system enforces a strict two-role permission hierarchy (**User** and **Administrator**), complete atomic transactional integrity, idempotency guards against duplicate submissions, dynamic fee calculation, quota restrictions, and auditable historical snapshots.

---

## 2. Core Features & Compliance Matrix

| Requirement | Implemented Feature | Description |
| :--- | :--- | :--- |
| **FR1 / BR10** | **Simulated Role Selector** | Instantaneous switching between synthetic users (`U001`, `U002`) and administrator (`A001`). Role ownership enforced at the backend API level. |
| **FR2 / BR2** | **Catalog & Real-time Capacity** | Displays available certificate services with live capacity counters and active status verification. |
| **FR3 / BR5** | **Certificate Request Form** | Captures applicant name, 10-digit mobile number, institutional reference, purpose, and base values with strict validation. |
| **FR4 / BR4** | **Dynamic Fee Calculator** | Computes fee in real-time: Base value < ₹1,000 charges ₹50; Base value $\ge$ ₹1,000 charges ₹0; non-chargeable charges ₹0. |
| **FR5 / BR1** | **Active Quota Limit (Max 5)** | Limits each user to a maximum of 5 concurrent active requests (`SUBMITTED`, `APPROVED`, `IN_PROGRESS`). Rejects the 6th. |
| **FR6 / BR7** | **Atomic Submission & Idempotency** | Prevents duplicate submissions using unique idempotency keys. Atomically decrements capacity, saves request, and logs status. |
| **FR7 / BR10** | **User Requests Isolation** | Applicants view and track only their own requests with complete status and fee information. |
| **FR8 / BR9** | **Eligible Cancellation** | Users may cancel requests if and only if in `SUBMITTED` status. Exactly one capacity unit is restored. Repeated cancellation rejected. |
| **FR9 / BR10** | **Administrator Audit Board** | Administrative officers inspect institutional request queues, applicant snapshots, and timeline progression. |
| **FR10 / BR8** | **Strict Status State Machine** | Sequential progression enforced: `SUBMITTED` $\rightarrow$ `APPROVED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`. Stage skipping prohibited. |
| **BR3** | **Immutable Historical Snapshot** | Persists JSON snapshot at the exact moment of submission, safeguarding against future master data alterations. |

---

## 3. Technology Stack

- **Backend Framework:** FastAPI 0.143.0 (Python 3.11+ / 3.13 compatible)
- **Database Engine:** SQLite 3 (ACID-compliant relational storage)
- **ORM:** SQLAlchemy 2.1.4
- **Template Engine:** Jinja2 3.1.6
- **Frontend Design:** HTML5, CSS3, Bootstrap 5.3.3, Bootstrap Icons, Vanilla JavaScript
- **Test Automation:** Pytest 9.1.1, FastAPI TestClient (HTTPX)
- **Modeling:** PlantUML 0.3.0 & Java Runtime
- **Version Control:** Git

*No unnecessary heavy frameworks (React, Docker, Redis, Celery, or external payment gateways) are utilized, ensuring clear architectural explainability during viva examinations.*

---

## 4. Prerequisites

1. **Python 3.11+** installed (tested on Python 3.13.14).
2. **Pip** package manager.
3. **Git** for version control.
4. *(Optional for re-compiling UML)* **Java SE Runtime** for PlantUML.

---

## 5. Installation Commands

Clone or navigate to the repository directory and set up a virtual environment:

```bash
# Navigate to project directory
cd "Certificate Submission SE"

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 6. Database Initialization & Seeding

The application automatically seeds the SQLite database upon first startup. To explicitly run the repeatable seeder script:

```bash
python scripts/seed_data.py
```

*The seeder script is idempotent: it never duplicates accounts or overwrites existing requests.*

---

## 7. How to Start the Application Server

Start the FastAPI application using Uvicorn:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 8. Application Access URLs

- **Web Application Portal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **User Dashboard:** [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- **Administrator Queue:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- **Role Switcher / Accounts:** [http://127.0.0.1:8000/accounts](http://127.0.0.1:8000/accounts)
- **Interactive OpenAPI Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 9. Pre-Seeded Sample Accounts

| Account ID | Full Name | System Role | Account Status | Phone |
| :--- | :--- | :--- | :--- | :--- |
| **U001** | Demo User One | USER | ACTIVE | 9876543210 |
| **U002** | Demo User Two | USER | ACTIVE | 9876543211 |
| **A001** | Demo Administrator | ADMINISTRATOR | ACTIVE | 9876543212 |

---

## 10. Pre-Seeded Service Catalog (Resources)

| Service ID | Certificate Service Name | Available Capacity | Catalog Status | Base Value | Fee Applied |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **S101** | Certificate Request A | 10 | ACTIVE | ₹500.00 | Yes (< ₹1000 $\rightarrow$ ₹50) |
| **S102** | Certificate Request B | 5 | ACTIVE | ₹1,500.00 | Yes ($\ge$ ₹1000 $\rightarrow$ ₹0) |
| **S103** | Certificate Request C | 0 | INACTIVE | ₹0.00 | No (Always ₹0) |

---

## 11. Viva Demonstration Procedure

### Workflow 1: User Request Creation & Idempotency
1. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) (defaults to `U001`).
2. Click **"New Request"** (`/requests/new`).
3. Select **Certificate Request A (`S101`)**. Notice initial capacity is 10.
4. Enter base value `500.00`. Notice the dynamic charge preview displays **₹50.00** with explanation.
5. Enter base value `1200.00`. Notice the dynamic charge preview changes to **₹0.00** (waived per BR4).
6. Fill in mandatory fields (Name, 10-digit phone, reference, description) and submit.
7. Observe redirection to the Request Details page (`/requests/{id}`) showing the status `SUBMITTED`, reserved capacity flag, and immutable snapshot card.

### Workflow 2: Eligible Cancellation & Capacity Return
1. From the Request Details or **"My Requests"** screen, click **"Cancel Request"**.
2. Notice the status transitions to `CANCELLED` and `resource_released` becomes true.
3. Check the catalog capacity on the Dashboard: the 1 reserved unit has been safely returned.
4. Try to cancel again: the action is rejected per BR9.

### Workflow 3: Administrator Sequential Progression & Anti-Skipping
1. Click the top-right profile dropdown and select **"Demo Administrator (A001)"**.
2. Navigate to the **Admin Queue** (`/admin`).
3. Find a `SUBMITTED` request and click **"Approve"** $\rightarrow$ status advances to `APPROVED`.
4. Click **"Start Progress"** $\rightarrow$ status advances to `IN_PROGRESS`.
5. Click **"Mark Completed"** $\rightarrow$ status advances to `COMPLETED`.
6. Notice that stage skipping is impossible: all stages must be completed sequentially per BR8.

---

## 12. Automated Testing

All 12 required test scenarios (T1–T12) are automated and executed with Pytest.

To run the complete test suite:

```bash
pytest -v
```

To run with coverage or output logging:

```bash
pytest -v > docs/evidence/test_run.log
```

### Test Suite Summary:
- **T1:** Duplicate submission idempotency guard (**PASS**)
- **T2:** Active request boundary checks (4, 5 allowed; 6th rejected) (**PASS**)
- **T3:** Submission against inactive/ineligible resource rejected (**PASS**)
- **T4:** Monetary fee boundary rules (₹999 $\rightarrow$ ₹50, ₹1000 $\rightarrow$ ₹0, ₹1001 $\rightarrow$ ₹0) (**PASS**)
- **T5:** Complete atomic submission workflow (**PASS**)
- **T6:** Field validation rejection without partial updates (**PASS**)
- **T7:** Pre-acceptance resource state change detection (**PASS**)
- **T8:** User cross-access and administrative privilege isolation (**PASS**)
- **T9:** Sequential stage progression and anti-skipping validation (**PASS**)
- **T10:** Cancellation double-action prevention (**PASS**)
- **T11:** Cross-process application restart persistence verification (**PASS**)
- **T12:** Immutable snapshot integrity against master data edits (**PASS**)

---

## 13. UML Diagrams

The project includes exactly two comprehensive UML diagrams conforming to the specification:

1. **Use Case Diagram:**
   - Source: [`docs/use_case.puml`](docs/use_case.puml)
   - Rendered Image: [`docs/use_case.png`](docs/use_case.png)
2. **Class Diagram:**
   - Source: [`docs/class_diagram.puml`](docs/class_diagram.puml)
   - Rendered Image: [`docs/class_diagram.png`](docs/class_diagram.png)

---

## 14. Project Directory Layout

```text
certificate-request-system/
├── app/
│   ├── database.py             # SQLite engine, session, and base definitions
│   ├── main.py                 # FastAPI application and lifespan events
│   ├── models/                 # SQLAlchemy ORM models (User, Resource, Request, History)
│   ├── schemas/                # Pydantic validation schemas
│   ├── services/               # Business logic (ValidationService, RequestService)
│   ├── routers/                # API and Template routers (auth, requests, admin, views)
│   ├── templates/              # Jinja2 HTML5 Bootstrap templates
│   └── static/                 # CSS styling and Vanilla JS scripts
├── docs/
│   ├── requirement_analysis.md # SRS, functional & business rules, RTM
│   ├── architecture.md         # 4-tier layered architecture documentation
│   ├── database_schema.md      # Relational database table schemas and constraints
│   ├── use_case.puml & .png    # Use Case Diagram
│   ├── class_diagram.puml &.png# Class Diagram
│   ├── test_cases.md           # T1–T12 detailed test case specifications
│   ├── test_execution_report.md# Formal test execution results
│   ├── ai_test_report.md       # AI prompt interaction and engineering report
│   ├── defect_log.md           # Defect tracker and resolution records
│   ├── ai_prompt_log.md        # Prompt interactions audit log
│   └── evidence/               # Real pytest execution logs
├── scripts/
│   └── seed_data.py            # Repeatable database seed script
├── tests/                      # Automated test suite (T1–T12)
├── pytest.ini                  # Pytest environment configuration
├── requirements.txt            # Pinned dependencies
├── README.md                   # Comprehensive project documentation
└── .gitignore                  # Git ignore rules
```

---

## 15. Known Limitations & Future Roadmap

- **Simulated Authentication:** Production OAuth/JWT authentication is abstracted via simulated session cookies per project guidelines.
- **Single Node Concurrency:** SQLite is optimal for prototype and academic demonstration; enterprise clustering should transition to PostgreSQL.

---

## 16. GitHub Submission Instructions

To push this repository to GitHub:

```bash
# 1. Initialize remote repository URL
git remote add origin https://github.com/<your-username>/<your-repo-name>.git

# 2. Rename branch to main if required
git branch -M main

# 3. Push commits to GitHub
git push -u origin main
```
