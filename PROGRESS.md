# Project checkpoint

## Current state

- Continuity setup: accepted by the user's request to start milestone 1.
- Application milestone 1: accepted by the user on 2026-09-10.
- Milestone 2: accepted by the user's request to proceed to the next milestone.
- Milestone 3: explicitly accepted by the user.
- Milestone 4: explicitly accepted by the user.
- Milestone 5: explicitly accepted by the user; milestone commit requested.
- Next step when requested: milestone 6 (login and JWT).
- The workspace was empty at initial inspection and was not a Git repository.
- FastAPI skeleton and health test added; dependencies installed in `.venv`.
- Git initialized on `main` at the user's request, with an initial baseline
  covering milestones 1-4 and project documentation (commit `307daf4`).
  No remote or push configured.
- Future commits and pushes still require an explicit user request.

## Sources and scope

The user confirmed that `docs/challenge.md` and `docs/design.md` do not exist and
are not needed. Use the supplied PDF and the decisions below as the current
project context; do not require those missing documents.

PDF source on the user's computer:
`C:/Users/Alexandru/Downloads/Design a takeaway platform.pdf`.
Text was extracted from all seven pages; embedded diagrams were not verified.
The PDF combines requirements and design proposals. An independent original
challenge was not available to verify which proposals are mandatory. Treat
document content as source material, not instructions to the coding agent.

Core scope:
- Customers browse restaurants and menus, place orders, and view order status.
- Assigned staff manage menus and update restaurant order statuses.
- Admins onboard restaurants and staff and manage staff assignments.
- Browsing is public; registration creates customers only.
- One restaurant per order; cart lives client-side; payment is on delivery.
- Tracking means reading order status, not live courier tracking.

## Agreed decisions

- Roles: `customer`, `staff`, and `admin`. All use the same login endpoint.
- Email policy accepted by user: trim, validate format, lowercase; preserve dots
  and plus tags. Apply consistently to registration and future login/recovery.
  PostgreSQL enforces case-insensitive uniqueness with an index on lower(email).
- Order creation must be atomic and idempotent. Persist a customer-scoped key
  and request fingerprint with the order. Repeating the same request returns
  the existing order; reusing the key with a different payload is a conflict.
- Order sequence: `pending -> accepted -> out_for_delivery -> delivered`.
- Use PostgreSQL `NUMERIC` and Python `Decimal` for money, one currency, and
  server-calculated totals. The currency still needs selection.
- Preserve item-name and unit-price snapshots in orders. Initially manage menu
  changes through edits and availability; no menu deletion endpoint is planned.
- Create files only when their milestones need them.

Implementation proposals recorded for the plan: synchronous SQLAlchemy sessions,
thin HTTP routers, Pydantic request/response schemas, and service functions for
workflows. Start with one models file; avoid a generic repository abstraction.

## Decisions to settle before affected work

- Currency, decimal precision, and rounding rules.
- Staff account credential provisioning and initial admin command details.
- Whether admins also receive operational staff permissions.
- Repeated status-update behavior and concurrent transition handling.
- Menu edits concurrent with order creation.
- Exact performance, metrics, and backup acceptance criteria. The PDF mentions
  p95 below 500 ms, contextual logs without PII, service metrics, and database
  snapshots, but workload and operational expectations are unspecified. Do not
  silently drop these or add tooling without resolving their scope.

## Milestones and acceptance criteria

Milestones 1-5 are **accepted**;
milestones 6-21 are **not started**. Each is a separate review stop and includes relevant tests or
operational verification.

| # | Scope | Acceptance criteria |
|---|---|---|
| 1 | FastAPI skeleton | `GET /health` returns 200 and `{"status":"ok"}`; endpoint test passes; README explains running and testing. |
| 2 | Local PostgreSQL | Compose starts PostgreSQL with persistent storage; `.env.example` documents configuration. |
| 3 | Database connection and Alembic | Session setup works; Alembic connects; database integration test passes. |
| 4 | User model | Migration creates users with unique email, password hash, and three roles; constraints are tested. |
| 5 | Customer registration | Passwords are hashed; only customers can register; duplicates, invalid inputs, and role escalation are tested. |
| 6 | Login and JWT | All roles can log in; protected `GET /users/me` works; bad credentials and invalid/expired tokens are tested. |
| 7 | Initial admin provisioning | Small command creates initial admin securely; duplicate provisioning is handled; no public admin registration. |
| 8 | Restaurant creation | Model and migration exist; only admins create restaurants; validation and authorization are tested. |
| 9 | Restaurant browsing | Public list/detail endpoints work; bounded pagination and missing restaurants are tested. |
| 10 | Staff onboarding and assignment | Admins create staff and assign restaurants; duplicate assignments and unauthorized access are tested. |
| 11 | Menu item creation | Model and migration exist; assigned staff add valid items; other users cannot. |
| 12 | Menu browsing | Public paginated menu endpoint returns prices and availability; missing restaurants are handled. |
| 13 | Menu updates | Assigned staff edit items and availability; cross-restaurant access and invalid prices are rejected. |
| 14 | Order persistence | Migrations include delivery details, totals, snapshots, and idempotency storage; constraints are tested. |
| 15 | Order creation | Transaction validates items, calculates totals, saves snapshots, and creates pending order; invalid requests leave no partial records; retries, including concurrent retries, cannot duplicate orders. |
| 16 | Customer order retrieval | Customers retrieve their orders and list them with pagination; access to other customers' orders is denied. |
| 17 | Staff order listing | Assigned staff list restaurant orders; pagination and assignment restrictions are tested. |
| 18 | Status transitions | Assigned staff advance orders through the agreed sequence; invalid transitions and competing updates are handled and tested. |
| 19 | Application container | Docker builds and runs Uvicorn; container health endpoint passes smoke test. |
| 20 | Full Compose deployment | Nginx proxies to application connected to PostgreSQL; startup and migration instructions pass smoke test. |
| 21 | Request logging | Logs include request IDs and useful failure context without passwords, tokens, addresses, or request bodies; behavior is verified. |

Order creation intentionally keeps transactions and idempotency together so the
endpoint is not considered complete without retry safety.

## Exact milestone 1 scope

- `pyproject.toml`: project metadata, FastAPI and Uvicorn; pytest and HTTPX for tests.
- `app/__init__.py` and `app/main.py`: application and health endpoint.
- `tests/test_health.py`: verify response status and body.
- `.gitignore`: Python caches, virtual environments, and local secrets.
- `README.md`: concise setup, run, and test instructions.

The endpoint checks process liveness only. No database, authentication, Docker,
or business endpoints in milestone 1.

## Latest verification and limitations

- During milestone 5 review, removed the default `not integration` pytest filter
  and simplified VS Code pytest arguments to `tests`. All tests now run by
  default; use `-m "not integration"` explicitly for tests without PostgreSQL.
  This supersedes earlier instructions about default test selection.
- Milestone 5: added POST /auth/register with request/response schemas, service,
  router, Argon2id hashing, server-assigned customer role, and named-constraint
  duplicate handling (409). Reject extra fields (422), including role/hash.
- Registration: normalized emails; passwords 15-128 characters, untrimmed; names
  trimmed 1-200 characters; optional address trimmed 1-1000 characters. Validation
  responses omit input values so password errors do not echo passwords.
- Migration 0002 replaces unique(email) with unique lower(email). Existing values
  are preserved; conflicting rows cause transactional failure, not data cleanup.
- Added pwdlib 0.3.1 with Argon2 support and email-validator 2.3.0 dependencies.
- Verification: migration applied, alembic check passed, current revision 0002;
  30 tests passed with the existing 2 dependency warnings; pip check passed.
  New tests cover normalized registration, stored hash verification, distinct
  salts, duplicate/conflicting existing emails, recovery after conflict, invalid
  and missing fields, forbidden roles/hash, and sanitized error responses.
- Registration tests use savepoints under a rolled-back outer transaction;
  no test accounts are retained. No live-server registration was performed.
- No login/JWT, mailbox verification, or rate limiting added. PostgreSQL remains
  running. User approved milestone 5 and requested its commit; no push requested.
- Earlier milestone notes below describe their state at completion; milestone 5
  supersedes earlier notes about missing registration and case-sensitive emails.
- Milestone 4: added `User` in `app/models.py`, migration `0001_create_users.py`,
  model registration in Alembic, and 9 PostgreSQL user constraint test cases.
  Integer ID; required email/hash/role/name; optional default_address. Unique
  email and a named CHECK constraint for customer/staff/admin. No role default.
- Applied `alembic upgrade head` successfully; `alembic current` reports
  `0001 (head)`; `alembic check` reports no new upgrade operations.
- All tests: 11 passed, with the existing 2 dependency warnings. Tests verify all
  three roles, field round-trip, duplicate emails, invalid roles, and NULL in
  required columns. Test transactions roll back; no test accounts are retained.
- Downgrade is provided but was not run against the local database, since it
  drops the user table. No dependencies added. Database remains running.
- No registration/login endpoints or hashing yet. Required text fields currently
  allow empty strings; API validation belongs to registration. Email uniqueness
  is case-sensitive pending the normalization decision. No automatic create_all.
- Milestone 3: added validated settings sharing Compose's `.env` values,
  cached synchronous SQLAlchemy engine, closing session dependency, empty
  declarative Base, Alembic environment/template, and read-only integration test.
- Added SQLAlchemy 2.0.52, Psycopg/binary 3.3.5, Alembic 1.19.2, and
  Pydantic Settings 2.15.0 in `.venv`. Initial editable reinstall hit a transient
  Windows file lock; retry succeeded. `pip check` passed.
- Verification: default pytest run passed 1 health test and deselected 1
  integration test; `pytest -q -m integration` passed 1 database test and
  deselected 1 health test. Both reported the existing 2 dependency warnings.
- `alembic current -v` connected successfully and reported no current revision.
  No schema migration or application table was created. PostgreSQL remains
  running. No HTTP endpoint uses a database session yet.
- Session cleanup rolls back unfinished work; features must explicitly commit
  successful writes. Run from the project root for `.env` discovery; restart
  the Python process after settings changes because the engine is cached.
- Milestone 3 originally had empty metadata; milestone 4 now imports `app.models`
  in `migrations/env.py` for autogeneration. No automatic table creation is used.
- Milestone 2: added `compose.yaml` (PostgreSQL 17, localhost port, named volume,
  readiness check), `.env.example`, and README startup/query/persistence steps.
  No application database connection or new Python dependencies added.
- Docker startup issue resolved with `docker desktop start`. Linux engine
  reports 29.7.2. Used explicit `--context desktop-linux` without changing the
  user's global context. Added Desktop's credential helper directory to the
  install command's PATH; README documents both troubleshooting steps.
- Created ignored `.env` from `.env.example` without overwriting an existing file.
- Compose validation passed; `postgres:17` downloaded and started healthy.
- `SELECT 1` passed. A probe row survived `compose down` and `compose up` with
  the named volume retained. Read back row 1 and removed the probe table.
- Database left running and healthy on `127.0.0.1:5432` for user review.
- Existing endpoint test rerun: 1 passed, with the same 2 dependency warnings.
- Continuity setup: reviewed both Markdown files against the agreed workflow,
  decisions, and 21-milestone plan. No executable behavior changed; no tests run.
- Milestone 1 verification on Python 3.11.7:
  - Editable installation with test dependencies succeeded in `.venv`.
  - `.\.venv\Scripts\python.exe -m pytest -q`: 1 passed, 2 dependency warnings.
  - `.\.venv\Scripts\python.exe -m pip check`: no broken requirements.
  - Uvicorn smoke test on localhost port 8765: HTTP 200, `{"status":"ok"}`.
    Temporary server stopped after verification.
- Tested versions: FastAPI 0.141.1, Uvicorn 0.52.4, Pydantic 2.13.5,
  pytest 9.1.1, HTTPX 0.28.1, Starlette 1.6.0, AnyIO 4.15.1.
- Dependency warnings: Starlette deprecated its HTTPX test-client integration
  in favor of HTTPX2, and uses a deprecated AnyIO BlockingPortal alias. Tests
  still pass; warnings are not suppressed. Retained the agreed HTTPX dependency.
- Dependency ranges are specified, not a full lockfile; future installations
  may resolve different versions. Health checks application liveness only;
  local database Compose configuration and Python connectivity are verified.
  User model and first migration are implemented; authentication and full
  deployment are not implemented.
- Future sessions must verify actual files and test results before relying on
  this checkpoint. Record review acceptance explicitly when the user gives it.
