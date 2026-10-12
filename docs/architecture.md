# System Architecture Documentation

**Project:** Certificate Request Management System  
**Institution:** Sri Eshwar College of Engineering  
**Architecture Pattern:** Layered Architectural Pattern (Presentation, Routing/API, Service/Domain, Data Persistence)  

---

## 1. Architectural Layers

The application follows a clean 4-tier modular architecture designed for high maintainability, clear separation of concerns, and ease of demonstration during viva examinations:

```text
+-----------------------------------------------------------------------+
|                         PRESENTATION LAYER                            |
|    Jinja2 HTML5 Templates | Bootstrap 5 | Vanilla JS | CSS Tokens      |
|    - Account Switcher     - User Dashboard      - Create Request Form  |
|    - My Requests List     - Request Details     - Admin Queue Board    |
+-----------------------------------------------------------------------+
                                    | HTTP / JSON / Form Data
+-----------------------------------------------------------------------+
|                       ROUTING & CONTROLLERS (API)                     |
|    FastAPI Routes (auth, requests, admin, views)                      |
|    - Request Parsing      - Role Verification    - Response Rendering |
+-----------------------------------------------------------------------+
                                    | Python Method Invocations
+-----------------------------------------------------------------------+
|                       SERVICE & BUSINESS LOGIC                        |
|    - ValidationService: Quota limits, Field regex, Charge calculation |
|    - RequestService: Atomic submission, Idempotency, Transitions      |
+-----------------------------------------------------------------------+
                                    | SQLAlchemy 2.0 ORM
+-----------------------------------------------------------------------+
|                       DATA ACCESS & PERSISTENCE                       |
|    SQLite Relational Engine | ACID Transactions | CHECK Constraints   |
|    - users      - resources      - service_requests    - history      |
+-----------------------------------------------------------------------+
```

---

## 2. Key Architecture Mechanisms

### 2.1 Atomic Transactions and Concurrency
All multi-table state updates are executed within explicit SQLAlchemy session transaction blocks (`with db.begin():` or manual `commit()` with rollback guards). For example, during request creation:
1. Active request count is queried within the transaction boundary.
2. Resource capacity is re-checked and updated atomically with conditional decrement (`UPDATE resources SET capacity = capacity - 1 WHERE id = :id AND capacity > 0`).
3. Request is inserted with a unique idempotency key.
4. History record is created.
5. All updates succeed together or roll back completely on any validation or constraint violation.

### 2.2 Idempotency Strategy
Accidental double-clicks or retried network requests present an `idempotency_key` (generated as a client-side UUID upon opening the create request form).
- If a request with the same idempotency key already exists, the backend intercepts the unique key constraint or checks existing records and returns the existing request safely without decrementing resource capacity a second time.

### 2.3 Role Authorization & Identity Simulation
Since production OAuth/SSO is out of scope per academic specification, active actor identity is maintained via a simulated session cookie (`session_user_id`). The backend validates actor role and identity on every sensitive endpoint:
- User endpoints enforce that applicants cannot access or cancel records belonging to other users.
- Administrative endpoints reject non-admin actors with HTTP 403 Forbidden.

### 2.4 Immutable Historical Snapshots
Master data in the `resources` table (e.g., certificate base value or service name) may change over time. To ensure audit integrity, a comprehensive JSON snapshot (`snapshot_data`) is stored directly on the `service_requests` row at the moment of submission, guaranteeing that subsequent alterations to master tables never distort past transactions.
