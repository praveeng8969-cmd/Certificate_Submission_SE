# Database Schema Documentation

**Project:** Certificate Request Management System  
**Database Engine:** SQLite (ACID-compliant relational database)  
**ORM:** SQLAlchemy 2.0  

---

## 1. Tables Overview

The database comprises four relational tables designed to ensure referential integrity, auditability, and atomic reservation handling:

1. `users`: Stores registered actors (applicants and administrators).
2. `resources`: Master catalog of certificate services, capacities, and charging policies.
3. `service_requests`: Immutable transaction records for submitted certificate requests.
4. `request_status_history`: Comprehensive audit trail recording every state transition.

---

## 2. Table Specifications

### 2.1 Table: `users`

Represents system actors and role authorization boundaries.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique user identifier (e.g., `U001`, `A001`). |
| `name` | VARCHAR(100) | NOT NULL | Full name of the user. |
| `role` | VARCHAR(20) | NOT NULL, CHECK(`role` IN ('USER', 'ADMINISTRATOR')) | Role privilege level. |
| `status` | VARCHAR(20) | NOT NULL, CHECK(`status` IN ('ACTIVE', 'INACTIVE')) | Account active status. |
| `phone` | VARCHAR(15) | NOT NULL | Primary contact phone number. |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation timestamp. |

---

### 2.2 Table: `resources`

Represents certificate service types, available quotas, and fee rules.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Service code (e.g., `S101`, `S102`, `S103`). |
| `service_name`| VARCHAR(150) | NOT NULL | Certificate service name. |
| `capacity` | INTEGER | NOT NULL, CHECK(`capacity` >= 0) | Available reservable units. |
| `status` | VARCHAR(20) | NOT NULL, CHECK(`status` IN ('ACTIVE', 'INACTIVE')) | Catalog operational status. |
| `base_value` | NUMERIC(10, 2)| NOT NULL, DEFAULT 0.00 | Standard nominal certificate value. |
| `charge_applicable`| BOOLEAN | NOT NULL, DEFAULT 1 | Whether monetary charge applies. |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp. |
| `updated_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp. |

*Constraint Guarantee:* The `CHECK(capacity >= 0)` constraint prevents concurrent over-allocation at the database engine level.

---

### 2.3 Table: `service_requests`

Stores certificate requests submitted by users, tracking lifecycle states, monetary charges, and immutable snapshots.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique request identifier (UUID or formatted code). |
| `user_id` | VARCHAR(36) | NOT NULL, FOREIGN KEY (`users.id`) | Submitting user ID. |
| `resource_id`| VARCHAR(36) | NOT NULL, FOREIGN KEY (`resources.id`)| Requested service ID. |
| `name` | VARCHAR(100) | NOT NULL | Applicant name at submission time. |
| `phone` | VARCHAR(15) | NOT NULL | 10-digit phone number. |
| `description`| TEXT | NOT NULL | Purpose/details of certificate request. |
| `reference` | VARCHAR(100) | NOT NULL | Institutional registration/reference ID. |
| `base_value` | NUMERIC(10, 2)| NOT NULL | Base value applied. |
| `service_charge`| NUMERIC(10, 2)| NOT NULL | Calculated service charge. |
| `status` | VARCHAR(20) | NOT NULL, CHECK(`status` IN ('SUBMITTED', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')) | Current request state. |
| `snapshot_data`| JSON | NOT NULL | Immutable JSON snapshot of submitted parameters. |
| `idempotency_key`| VARCHAR(100)| NOT NULL, UNIQUE | Unique submission key to prevent duplicates. |
| `resource_reserved`| BOOLEAN | NOT NULL, DEFAULT 1 | True if 1 capacity unit was reserved. |
| `resource_released`| BOOLEAN | NOT NULL, DEFAULT 0 | True if unit was returned via cancellation. |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Submission timestamp. |
| `updated_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Status update timestamp. |

*Indexes:*
- `ix_service_requests_user_id` on `user_id`
- `ix_service_requests_resource_id` on `resource_id`
- `ix_service_requests_status` on `status`
- `uq_service_requests_idempotency_key` UNIQUE on `idempotency_key`

---

### 2.4 Table: `request_status_history`

Audit ledger recording every status change with exact timestamps and initiating actors.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Monotonic audit sequence ID. |
| `reference_id`| VARCHAR(36)| NOT NULL, FOREIGN KEY (`service_requests.id`)| Associated request ID. |
| `actor_id` | VARCHAR(36) | NOT NULL, FOREIGN KEY (`users.id`)| ID of the actor performing the transition. |
| `old_status` | VARCHAR(20) | NULLABLE | Pre-transition status (NULL on creation). |
| `new_status` | VARCHAR(20) | NOT NULL | Target state reached. |
| `event_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Exact transition timestamp. |

*Indexes:*
- `ix_history_reference_id` on `reference_id`

---

## 3. Entity-Relationship Diagram (Textual Representation)

```text
[users] 1 --------< N [service_requests] >-------- 1 [resources]
   |                          |
   |                          1
   |                          |
   +------------< N [request_status_history]
```

## 4. Seeding Specifications

On database initialization:
1. `users`:
   - `U001`: Demo User One (Role: `USER`, Status: `ACTIVE`, Phone: `9876543210`)
   - `U002`: Demo User Two (Role: `USER`, Status: `ACTIVE`, Phone: `9876543211`)
   - `A001`: Demo Administrator (Role: `ADMINISTRATOR`, Status: `ACTIVE`, Phone: `9876543212`)
2. `resources`:
   - `S101`: Certificate Request A (Capacity: 10, Status: `ACTIVE`, Base Value: ₹500.00, Charge Applicable: True)
   - `S102`: Certificate Request B (Capacity: 5, Status: `ACTIVE`, Base Value: ₹1500.00, Charge Applicable: True)
   - `S103`: Certificate Request C (Capacity: 0, Status: `INACTIVE`, Base Value: ₹0.00, Charge Applicable: False)
