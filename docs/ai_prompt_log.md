# AI Prompt & Engineering Interaction Log

**Project:** Certificate Request Management System  
**Institution:** Sri Eshwar College of Engineering  
**Assessment:** Software Engineering SAT II — Case 43  

---

## Session Log Summary

This document records the structured interaction prompts and architecture engineering decisions utilized during the full-stack design, implementation, and automated testing of the Certificate Request Management System.

### Interaction 1: Architecture & Data Modeling
- **Prompt Theme:** Database Schema and SQLAlchemy Entity Definitions
- **Design Intent:** Translate FR1–FR10 and BR1–BR10 into relational database entities with strict check constraints, foreign keys, and atomic capacity limits.
- **AI Recommendation:** Establish four tables: `users`, `resources`, `service_requests`, and `request_status_history`. Include `CHECK (capacity >= 0)` and `CHECK (status IN (...))` constraints.
- **Engineering Review & Action:** Approved and implemented in `app/models/`.

### Interaction 2: UML Modeling (Use Case & Class Diagrams)
- **Prompt Theme:** PlantUML diagrams conforming to strict two-actor role system
- **Design Intent:** Represent Actors (User, Administrator), Use Cases with `<<include>>` and `<<extend>>` semantics, and Class Diagram with exact attributes, methods, and multiplicities.
- **AI Recommendation:** Generated PlantUML scripts for `docs/use_case.puml` and `docs/class_diagram.puml` and compiled to PNG assets using the PlantUML compiler.
- **Engineering Review & Action:** Verified that exactly two UML diagrams were created, both rendered to PNG.

### Interaction 3: Atomic Business Services & Idempotency Protection
- **Prompt Theme:** Idempotency Key Handling, Quota Validation, and State Machine Progression
- **Design Intent:** Guarantee that re-submitting an existing idempotency key yields the prior request without double-decrementing capacity. Enforce max 5 active requests (SUBMITTED, APPROVED, IN_PROGRESS).
- **AI Recommendation:** Implemented in `ValidationService` and `RequestService` using conditional SQL update statements and explicit rollback guards.
- **Engineering Review & Action:** Tested and verified via test scenarios T1 and T2.

### Interaction 4: Test Suite & Real Process Persistence Check
- **Prompt Theme:** Automated Verification of Scenarios T1–T12
- **Design Intent:** Construct automated test suite covering all mandatory scenarios, including a true cross-process restart persistence check for T11.
- **AI Recommendation:** Utilized `pytest`, `TestClient`, and Python `subprocess` to spawn separate processes against persistent SQLite files.
- **Engineering Review & Action:** 100% test execution pass rate achieved.
