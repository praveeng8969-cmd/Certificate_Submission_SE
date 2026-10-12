# Requirement Analysis Document

**Project:** Certificate Request Management System  
**Institution:** Sri Eshwar College of Engineering  
**Assessment:** Software Engineering SAT II  
**Industry Use Case:** 43 — Certificate Request System  
**Academic Year:** 2025–2026  

---

## 1. Problem Summary

In higher education institutions and enterprise organizations, students and alumni routinely apply for official certificates (e.g., Bonafide, Transcript, Degree Verification, Medium of Instruction, Conduct Certificates). Traditional manual processing faces numerous challenges:
- Duplicate applications caused by accidental resubmissions or network jitter.
- Administrative bottlenecks without clear status transparency or request quota enforcement.
- Absence of real-time capacity monitoring and eligibility verification.
- Inconsistent fee assessments based on certificate categories and base valuations.
- Vulnerability to race conditions when concurrent requests exhaust the last available service slot.

The **Certificate Request Management System** provides an automated, reliable, and auditable web-based platform to facilitate seamless certificate requesting, validation, idempotency management, fee calculation, administrative processing, and verifiable status tracking.

---

## 2. Project Objectives

1. **Structured Request Lifecycle:** Implement a strict, non-skippable progression from creation through validation, approval, progress, and completion:
   $$\text{SUBMITTED} \longrightarrow \text{APPROVED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{COMPLETED}$$
2. **Quota and Eligibility Enforcement:** Strictly enforce user active request limits (maximum 5 active requests across the system) and resource capacity.
3. **Deterministic Fee Calculation:** Automate charge calculations with decimal-safe rules based on certificate chargeable status and base value thresholds.
4. **Idempotency & Concurrency Safety:** Prevent duplicate requests and race conditions via unique idempotency keys and atomic transactional integrity.
5. **Auditable Historical Snapshots:** Record an immutable snapshot of applicant details and service parameters at the instant of submission, safeguarding against downstream master-data modifications.
6. **Role-Based Access Control:** Secure user and administrator boundaries on both the frontend and backend API endpoints.

---

## 3. Actors and Responsibilities

| Actor | Description | Key Responsibilities |
| :--- | :--- | :--- |
| **User** | Registered student / applicant within the institution (e.g., Demo User One `U001`, Demo User Two `U002`). | - Select/switch authenticated user profile.<br>- Browse active certificate services with real-time capacity.<br>- Submit new certificate requests with applicant details.<br>- Preview charge summary prior to submission.<br>- Monitor request status timeline and immutable snapshot.<br>- Cancel eligible requests (only allowed in `SUBMITTED` status). |
| **Administrator** | Institutional administrative officer overseeing certificate dispatch (e.g., Demo Administrator `A001`). | - Review institutional queue of all certificate requests.<br>- Inspect submitted applicant snapshots and audit histories.<br>- Transition requests sequentially (`SUBMITTED` $\rightarrow$ `APPROVED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`).<br>- Strictly prohibited from skipping stages or modifying completed/cancelled requests. |

---

## 4. Scope and Exclusions

### In-Scope:
- Synthetic account switching between User 1 (`U001`), User 2 (`U002`), and Administrator (`A001`).
- Master catalog of certificate services (`S101`, `S102`, `S103`) with capacity quotas and active/inactive states.
- Client-side and server-side validation (applicant name, 10-digit phone, mandatory reference and description).
- Dynamic charge calculation (Base value < ₹1,000 charges ₹50; Base value $\ge$ ₹1,000 charges ₹0; non-chargeable charges ₹0).
- Atomic reservation of capacity upon submission and atomic single-release upon cancellation.
- Full transactional persistence with SQLite.
- Complete traceability and audit logging in `request_status_history`.
- Idempotency key tracking preventing duplicate form submissions.

### Exclusions:
- Third-party OAuth / SSO authentication (session-simulated role switcher utilized per project guidelines).
- Payment gateway integration (Stripe, Razorpay, etc.).
- External cloud messaging / SMS / email dispatch microservices.
- Multi-container Docker / Kubernetes clustering and Redis caching layers.

---

## 5. Functional Requirements (FR1 – FR10)

- **FR1: Role Selection & Session Simulation:** The system shall allow instantaneous switching between two synthetic user accounts (`U001`, `U002`) and one administrator account (`A001`), maintaining role context across requests.
- **FR2: Service Catalog & Capacity Display:** The system shall display all certificate services, their operational status (Active/Inactive), base values, and currently available reservable capacities.
- **FR3: Request Initiation & Input Capture:** The system shall provide an intuitive form capturing the chosen certificate service, applicant name, 10-digit phone number, description, academic reference, and base value.
- **FR4: Real-Time Fee Calculation:** The system shall compute and preview the applicable service charge dynamically prior to form submission following institutional business rules.
- **FR5: Pre-Submission Validation:** The system shall reject submissions with missing names, invalid phone lengths ($\ne 10$ digits), blank descriptions/references, inactive resources, or exceeded user quotas.
- **FR6: Atomic Submission with Idempotency:** The system shall create the request, store an immutable snapshot, decrement available resource capacity, set status to `SUBMITTED`, and write a history record within a single database transaction. Duplicate submissions with identical idempotency keys shall be returned without duplicating resource reservations.
- **FR7: User Request Monitoring:** The system shall allow users to view only their own submitted requests along with current status, reference ID, fee assessed, and submission timestamps.
- **FR8: Eligible Request Cancellation:** The system shall permit users to cancel requests if and only if they are in `SUBMITTED` status. Cancellation shall atomically release reserved resource capacity exactly once.
- **FR9: Administrator Queue & Historical Audit:** The system shall grant administrators unified visibility into all requests, their complete status progression timelines, applicant snapshots, and actor tracking.
- **FR10: Sequential Status Progression:** The system shall allow administrators to advance requests sequentially through the designated lifecycle (`SUBMITTED` $\rightarrow$ `APPROVED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`). Skipping stages or modifying terminal states shall be rejected.

---

## 6. Business Rules (BR1 – BR10)

- **BR1 (Active Request Limit):** A user may have at most **5 active requests** across the entire system. Any attempt to submit a 6th active request must be rejected.  
  *Active Statuses:* `SUBMITTED`, `APPROVED`, `IN_PROGRESS`.  
  *Inactive/Terminal Statuses:* `COMPLETED`, `CANCELLED`.
- **BR2 (Eligibility & Master Active Check):** Both the requesting user account and the target certificate resource must be in `ACTIVE` status. Validation must occur immediately before transaction commit.
- **BR3 (Immutable Historical Snapshot):** The system must persist a JSON snapshot containing applicant details, reference, base value, calculated charge, and resource metadata at submission time. Future updates to resource master data must not alter historical request data.
- **BR4 (Monetary Calculation Rules):**  
  - If resource `charge_applicable` is true:
    - Base value $< ₹1,000 \implies$ Service Charge = ₹50.00
    - Base value $\ge ₹1,000 \implies$ Service Charge = ₹0.00
  - If resource `charge_applicable` is false:
    - Service Charge = ₹0.00  
  All calculations must be decimal-safe.
- **BR5 (Mandatory Field Validations):** Applicant name cannot be blank. Phone number must consist of exactly 10 numeric digits. Description and Reference fields must not be empty or whitespace-only.
- **BR6 (All-or-Nothing Validation Failure):** Any validation failure must result in zero changes to the database: no request created, no status changes, and no resource capacity decremented.
- **BR7 (Atomic Submission Execution):** Submission must atomically:
  1. Verify resource capacity $> 0$ and active request limit $< 5$.
  2. Create request record with unique ID and idempotency key.
  3. Store immutable snapshot data.
  4. Decrement resource available capacity by 1.
  5. Set request status to `SUBMITTED`.
  6. Insert `request_status_history` record (`None` $\rightarrow$ `SUBMITTED`).
- **BR8 (Strict Status Lifecycle Progression):** Permitted state transitions:  
  $$\text{SUBMITTED} \longrightarrow \text{APPROVED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{COMPLETED}$$  
  $$\text{SUBMITTED} \longrightarrow \text{CANCELLED} \quad (\text{User cancellation only})$$  
  Skipping stages (e.g., `SUBMITTED` $\rightarrow$ `IN_PROGRESS`) or altering `COMPLETED`/`CANCELLED` requests is forbidden.
- **BR9 (Single Capacity Release on Cancellation):** Cancelling a request must transition status to `CANCELLED` and increment resource capacity by 1 exactly once. Subsequent cancellation requests on an already cancelled request must be rejected with no side effects.
- **BR10 (Backend Authorization Enforcement):** Users can only view and cancel their own requests. Only administrators can approve or advance requests. Authorization checks must be strictly enforced on backend service and API layers.

---

## 7. Non-Functional Requirements (NFR1 – NFR5)

- **NFR1: Reliability & Transactional Integrity:** The system must guarantee zero partial writes. Any runtime error during multi-table writes must trigger an immediate rollback.
- **NFR2: Data Persistence:** All data (users, resources, requests, history logs) must reside in persistent SQLite storage and remain fully consistent across application server restarts.
- **NFR3: Architectural Maintainability:** The software must enforce clean separation of concerns: Presentation (Jinja2 / Bootstrap), Routing & Serialization (FastAPI), Business Rules & Validation (Services), and Persistence (SQLAlchemy ORM).
- **NFR4: Usability & User Experience:** The UI must feature clean typography, professional blue accents, intuitive card-based dashboards, clear validation error feedback, and responsive layout for mobile and desktop screens.
- **NFR5: Backend Security by Design:** State changes and resource operations must be guarded by server-side role validation and ownership checks regardless of frontend caller manipulation.

---

## 8. System Assumptions

1. Synthetic users (`U001`, `U002`) and administrator (`A001`) are pre-seeded in active status.
2. Initial certificate catalog resources are seeded as:
   - `S101` — Certificate Request A — Capacity: 10 — Status: ACTIVE — Charge Applicable: True
   - `S102` — Certificate Request B — Capacity: 5 — Status: ACTIVE — Charge Applicable: True
   - `S103` — Certificate Request C — Capacity: 0 — Status: INACTIVE — Charge Applicable: False
3. Each accepted certificate request reserves exactly 1 capacity unit from the selected resource. Cancellation restores 1 unit.
4. Currency values are denominated in Indian Rupees (INR, ₹) with standard 2-decimal precision.

---

## 9. Requirement Traceability Matrix (RTM)

| Requirement ID | Description | UML Element | Implemented Feature / Code | Test ID |
| :--- | :--- | :--- | :--- | :--- |
| **FR1 / BR10** | Role switching & session authorization | `User`, `UseCase: Select user/admin account` | `app/routers/auth.py`, `app/services/request_service.py` | T8 |
| **FR2 / BR2** | Service catalog & capacity inspection | `Resource`, `UseCase: View available services` | `app/models/resource.py`, `app/routers/requests.py` | T3, T7 |
| **FR3 / BR5** | Certificate request creation & field checks | `ServiceRequest`, `ValidationService.validate_details()` | `app/services/validation_service.py`, `app/schemas/schemas.py` | T6 |
| **FR4 / BR4** | Dynamic fee calculation (₹50 vs ₹0) | `ValidationService.calculate_charge()` | `app/services/validation_service.py:calculate_charge()` | T4 |
| **FR5 / BR1** | Active quota limit enforcement (Max 5) | `ValidationService.validate_request_limit()` | `app/services/validation_service.py:validate_request_limit()` | T2 |
| **FR6 / BR7** | Atomic submission & idempotency protection | `RequestService.create_request()`, `ServiceRequest` | `app/services/request_service.py:create_request()` | T1, T5 |
| **FR7 / BR10** | User request list & data isolation | `RequestService.get_user_requests()` | `app/routers/requests.py:my_requests` | T8 |
| **FR8 / BR9** | User cancellation & single capacity restore | `RequestService.cancel_request()` | `app/services/request_service.py:cancel_request()` | T10 |
| **FR9 / BR10** | Admin queue & complete audit timeline | `RequestStatusHistory`, `RequestService.get_all_requests()` | `app/routers/admin.py`, `app/models/history.py` | T5, T9 |
| **FR10 / BR8** | Sequential stage transitions without skipping | `ValidationService.validate_transition()`, `RequestService.advance_status()` | `app/services/request_service.py:advance_status()` | T9 |
| **BR3** | Immutable snapshot storage | `ServiceRequest.snapshot_data` | `app/models/request.py:snapshot_data` | T12 |
| **NFR1 / NFR2**| Transactional persistence across restart | `database.py`, SQLite session transaction | `app/database.py`, `app/main.py` | T11 |
