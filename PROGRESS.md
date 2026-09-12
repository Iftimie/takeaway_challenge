# Project checkpoint

## Current state

- Continuity setup: accepted by the user's request to start milestone 1.
- Application milestone 1: accepted by the user on 2026-09-10.
- Milestone 2: accepted by the user's request to proceed to the next milestone.
- Milestone 3: explicitly accepted by the user.
- Milestone 4: explicitly accepted by the user.
- Milestone 5: explicitly accepted and committed (`5bdb865`).
- Milestone 6: explicitly accepted and committed (`b8e0cc3`).
- Milestone 7: explicitly accepted and committed (`c1d0dc2`).
- Milestone 8: explicitly accepted and committed (`668c6ca`).
- Milestone 9: explicitly accepted and committed (`e06de46`).
- Milestone 10: explicitly accepted and committed (`4d47e81`).
- Milestone 11: explicitly accepted and committed (`4800f89`).
- Milestone 12: explicitly accepted and committed (`04ebf47`).
- Milestone 13: explicitly accepted and committed (`cd836a3`).
- Milestone 14: explicitly accepted and committed (`7e2620a`).
- Milestone 15: explicitly accepted and manually committed by user (`ee91a55`).
- Milestone 16: explicitly accepted and manually committed by user (`f87b809`).
- Milestone 17: explicitly accepted and committed (`adec890`).
- Milestone 18: explicitly accepted and committed (`d7b105c`).
- Milestone 19: explicitly accepted and committed (`0b4e92c`).
- Milestone 20: explicitly accepted and committed (`1bfafa4`).
- Milestone 21: logging and schema-driven redaction accepted and committed (`965732a`).
- Redaction step 1: accepted by the user; emails intentionally left visible.
- Redaction step 2: schema-aware request/response logging accepted by the user.
  All 401 tests pass with two existing dependency warnings. No new dependencies
  or migrations. Payloads use the declared schema and redact marked fields;
  invalid requests log field locations/error types only. Unknown schemas are
  omitted. Each redacted payload is capped at 4 KiB, with a 64 KiB raw inspection
  ceiling; validation details include at most 20 errors and are also bounded.
  API responses remain unchanged. Unexpected failures omit bodies and retain
  exception class only. User requested the milestone 21 commit.
  Rebuilt Compose services are healthy. Live Nginx checks passed for registration,
  login, profile and invalid input: marked values absent from logs, email visible
  in app logs only, response IDs matched proxy logs. Temporary account removed.
- User explicitly skipped the proposed database backup milestone. Backups remain
  a production consideration, not an implementation task for this challenge.
- Performance/metrics scope remains unresolved; user switched focus to the UI epic.
- UI F1: accepted and committed (`0d6a777`). FastAPI serves /ui/ with pinned local
  Vue 3.5.13, plain CSS and hash navigation. Restaurants/login are placeholders.
  Static assets are included in Python packages and the existing Docker image.
  Verification: 11 focused UI/health/logging tests passed (2 existing warnings).
  Compose rebuild passed; browser through Nginx verified rendering, navigation,
  refresh of /ui/#/login and Back. No API integration or authentication yet.
  User requested two testing submilestones below.
  User requested simplified navigation: retain data, computed view and inline
  hashchange listener only. Removed dynamic tab titles, heading focus and listener
  cleanup; this shell stays mounted for the page lifetime. Unknown routes still
  show a fallback and the main navigation remains available.
  After simplification: 2 UI serving tests passed, 2 existing warnings. Browser
  checks above predate this simplification; Docker image has not been rebuilt.

## UI epic plan

F1 and F1.1 are accepted; F1.1 committed as `d940626`.
F1.2 is accepted and committed (`da4786a`). Added Playwright Test 1.63.0, lockfile,
Chromium-only config and two browser tests. Default run owns a temporary Uvicorn
server on port 8766; UI_BASE_URL targets an existing deployment instead.
Tests cover view navigation/Back/Forward and direct hash URL/refresh. One worker,
no retries, traces retained on failure. User enabled video recording for all tests;
preserved that setting. User finds traces sufficient for inspecting test actions;
use --trace on to retain passing traces. Node tooling stays outside the production image.
Local browser suite: 2 passed in 2.6s; benign NO_COLOR/FORCE_COLOR warning.
Compose rebuilt healthy; the same 2 tests passed through Nginx in 1.7s.
git diff --check passed. Backend/unit suites were not repeated for tooling-only
changes. Compose remains running; the temporary local test server was stopped.
F2 is accepted and committed (`297d89a`). Added handwritten fetch client and restaurant
state module, name/address list, pagination, loading/empty/error/retry.
Duplicate loads are prevented; Next respects API offset ceiling 10000. A full
last page may lead to one empty page because API has no total count. Previous
remains available. Hash navigation retains the list; refresh resets to page 1.
No menu browsing until F3, dependencies or backend changes.
Verification: 6 JS unit tests, 4 browser tests (controlled API responses), and
2 UI-serving tests passed; existing color/dependency warnings remain. Compose
rebuilt healthy; real browser smoke through Nginx loaded 3 existing restaurants.
User changed PAGE_SIZE to 2; retained. Follow-up adds a real-database browser test:
compose.browser-tests.yaml owns a separate PostgreSQL 17 container on 55432 with
tmpfs storage, fixed test-only database/user/password, and a separate Compose
project. Global setup starts it and applies Alembic; teardown removes it.
Python helper seeds 3 restaurants and commits for API visibility; finally cleanup
removes them. Each seed resets leftover fixture rows, restricted by fixed endpoint
and verified DB/user identity. No normal .env database settings used by helper.
Playwright app uses matching explicit test settings. UI_BASE_URL runs skip real
DB fixtures and run mocked tests only. No normal application data modified.
Updated pagination unit/mock tests for PAGE_SIZE=2. Verification: 6 unit tests and
5 browser tests passed (11.5s browser suite); Docker ps confirmed test container
removed. User approved F2, fixture setup/teardown and trace shortcuts for commit.
F3 menu browsing is accepted by the user; commit requested. View menu links use
#/restaurants/{id}/menu; show restaurant name, unchanged API price strings/EUR,
availability, 2-item pagination, loading/error/retry/empty/not-found states and
Back to restaurants. Menu visits reset page 1; restaurant list state is retained.
Separate state per menu visit prevents late responses overwriting another menu.
Fixtures seed 3 menu items (one unavailable) for restaurant 1, one for restaurant
2, and none for restaurant 3. Cleanup deletes menu rows before restaurants.
Real DB browser test covers pagination, availability, isolation, refresh, empty
menu and missing restaurant. No cart, authentication or backend changes.
Verification: 9 unit tests, 6 browser tests (14.1s) and 2 UI-serving tests passed;
existing color/dependency warnings remain. Compose rebuilt healthy for review.
Commit F3. Browser test titles must use dashes, as requested by the user.
Admin permission change accepted: admins bypass restaurant assignment checks for
menu creation/updates and restaurant order listing/status updates. Tests now
verify all four operations without assignments, missing restaurant 404 and status
transition rules. Existing customer/staff restrictions remain. 403 backend tests
passed with 2 existing warnings; separate commit requested by the user.
F3 committed as e9c0060. User revised F4: login must survive page refresh;
use tab-scoped sessionStorage and automatic /users/me validation on startup.
F4 accepted by the user; commit requested. Login form calls /auth/login then /users/me;
only commits session identity after both succeed. Header shows name and server
role, Account and Log out. Token persists in sessionStorage; logout clears it and
identity/form values. Password clears on submission/navigation. Startup checks
/users/me; 401 clears login and shows an expiry message. No background expiry
polling; future protected calls should reuse authenticatedFetch. Public browsing
remains available. No backend changes or new dependencies.
Fixtures add a test-only customer with a hashed password; clean removes it. Test
app JWT key is explicit and test-only. Real browser login covers invalid password,
success, logout and page-refresh preservation of login; only expired /users/me is mocked.
Refresh account button removed. Verification: 13 unit tests and 7 browser tests
passed (16.8s) after this revision. No F4 commit
requested; stop for review. Admin permission change committed as 8e51fde.
Two UI-serving tests also passed (2 existing warnings); Compose rebuild completed
healthy. Browser runs retain the existing benign color-environment warning.
User requested standard Vue single-file components and a frontend build. F4
refactor awaiting review: App.vue owns state/navigation; LoginView, RestaurantList
and MenuView use props/events. Behaviour retained. Vite 8.3.0/plugin-vue 6.0.8
build app/ui/dist served by FastAPI. Vue 3.5.13 installed via npm; vendored global
script removed. Node >=22.12 required; verified on 24.20.0. Docker has a Node
build stage and Python runtime; Python package data includes compiled assets.
npm run dev serves live UI with backend proxy; npm run build for local FastAPI.
Browser/trace npm commands build first. Verification: build, 13 unit tests and
7 browser tests passed. Two UI-serving tests passed (2 existing warnings).
Multi-stage Docker rebuild healthy; 4 browser checks passed through Nginx,
3 isolated-DB tests skipped as designed. F4 approved for commit, including Vue SFC
build refactor. F4 committed as 2ec3b7b.
F5 accepted and committed as cf328c9. RegisterView.vue and /register hash route,
customer email/password/name/optional address form. Uses existing API; explicit
payload excludes roles. Field validation, duplicate email, network/failure and
success feedback; success links to login without automatic authentication.
Password clears on submission; other inputs retained on errors and cleared on
success. Submit disabled while pending. Blank optional address becomes null.
No backend/dependency changes. Real isolated-DB browser journey covers validation,
duplicate email, successful creation and login as customer; teardown removes it.
Verification: 16 unit tests and 8 browser tests passed (20.7s). No F5 commit
requested; stop for review.
F5 follow-up verification: 2 UI-serving tests passed (2 existing warnings),
Docker Compose rebuild completed healthy and git diff --check passed.
F6 authorized: cart uses sessionStorage to survive refresh, as requested. Backend
limits are 100 distinct items and quantity 1-100 per item.
F6 accepted and committed as 01ddc6d. CartView and /cart route; add available items,
merge quantities, edit integer quantities 1-100, remove lines and cap distinct
items at 100. One restaurant per cart, browser confirmation before replacement.
Cart persists in sessionStorage; invalid stored data falls back to empty. Explicit
logout clears cart. Public browsing/cart works before login. Totals use integer
cents, labelled estimates; checkout will recheck server prices/availability.
No order submission until F7. No backend changes or new dependencies.
Verification: 20 unit tests and 9 browser tests passed (20.6s). Real seeded cart
journey covers unavailable items, quantity/total, refresh, replacement cancel/
confirm and removal persistence. User requested F7 after accepting F6.
Two UI-serving tests passed (2 existing warnings); Compose rebuilt healthy and
git diff --check passed. Browser tests retain the benign color warning.
Added requested trace shortcuts: npm run test:trace retains all test traces;
npm run trace lists current trace.zip archives and opens the selected number.
No additional dependencies; Enter cancels and missing traces show guidance.
F7 accepted and committed as c2ccfbb; user requested F8. Checkout route/component uses
the existing POST /orders API, customer access, profile delivery defaults and
server confirmation with order number/status/items/final total. Successful orders
clear the cart. Pending checkout stores the exact payload, customer ID and UUID
idempotency key in sessionStorage before sending. Network/5xx/401 failures retain
it across refresh; retries use the same request. Known 403/404/409/422 rejections
allow correction. Duplicate submissions are blocked. Pending cart editing is
blocked; logout retains unresolved checkout for its original customer to retry.
This intentionally qualifies F6's usual clear-cart-on-logout behavior. Delivery
details remain in tab storage until resolved; closing the tab loses recovery.
Confirmation itself is in memory; order history belongs to F8. No payment,
automatic retry, new dependencies or backend API changes.
Verification: 25 JS unit tests, all 10 browser tests (23.9s) and 2 UI-serving tests
passed. Checkout/login browser tests passed again after the final logout change
(2 tests, 13.4s). Real DB test commits an order, drops the response, refreshes and
retries: HTTP 200 returns the original ID and order listing contains one order.
Fixture cleanup now deletes order lines/orders before menus/restaurants/users.
Existing dependency and color warnings remain. Compose rebuilt healthy for
manual review; git diff --check passed. Stop for F7 review.
F8 accepted and committed as 56072b0; user requested F9. My orders navigation and /orders,
/orders/{id} hash views use existing customer-only APIs. Two orders per page,
newest first, detail snapshots/delivery/total/status and explicit Refresh.
Checkout confirmation links to its order. Loading, empty, missing, failure and
authentication states are handled. Each visit/account change gets separate state
so late responses cannot overwrite a new view. No stored order history or polling.
Restaurant IDs and server timestamps are displayed directly; list pagination
returns to page 1 after leaving the view. No backend or dependency changes.
Isolated browser fixtures optionally seed three orders; existing checkout tests
still start with no orders. Verification: 29 JS unit tests and 2 UI-serving tests
passed, with the existing Python dependency warnings. All 11 browser tests passed
(26.7s), including real history pagination/details/refresh/missing/logout checks.
Compose rebuilt healthy; git diff --check passed. Stop for F8 review.
F9 accepted and committed as 6d3a931; user requested F10. Staff/admin see a Manage menu
section below a restaurant's public menu. Create or select a current-page item
to edit name, decimal-string price and availability. Saves reload that page;
new items appear at the end of the existing two-item pagination. Form state is
per restaurant/account visit. Validation/errors and expired login use existing
patterns. API permissions remain authoritative: assigned staff or any admin.
Flagged API gap before implementation: no assigned-restaurant listing endpoint.
Staff browse the public list; unassigned saves show 403 feedback. No backend
changes or dependencies. Uncertain writes advise refreshing before retrying;
menu creation has no idempotency support. Navigation discards unsaved edits.
Isolated seed-menu fixtures add assigned staff and an admin; cleanup removes
assignments before users/restaurants. Browser journey checks create, edit price,
availability persistence, unassigned denial and admin access.
Verification: JS unit suite passed (32 tests); all 12 browser tests passed
(32.0s), and 2 UI-serving tests passed. Existing dependency/color warnings remain.
Compose rebuilt healthy. Stop for F9 review; no F9 commit requested yet.
F10 accepted including URL pagination and committed as 583980f; user requested F11. Manage orders link on restaurant
menus for staff/admin opens /restaurants/{id}/orders hash view. Two orders per
page, newest first; delivery details, purchased lines, totals and status shown.
Explicit Refresh, empty/loading/error states and API assignment checks. Next-step
buttons only: pending -> accepted -> out_for_delivery -> delivered. Server response
replaces the order snapshot. Conflict/uncertain update blocks further changes
until refresh; no automatic retries, polling, row locks or backend changes.
Separate state per restaurant/account visit prevents late responses replacing a
new view. Existing missing assignment-list API limitation remains as in F9.
Verification: 36 JS unit tests, all 13 browser tests (31.6s) and 2 UI-serving tests
passed. Real fixtures cover staff pagination, full status lifecycle, refresh
persistence and unassigned denial. Existing dependency/color warnings remain.
Compose rebuilt healthy; whitespace checks passed. Stop for F10 review.
F10 review revision: user requested URL pagination for restaurant orders only.
Next/Previous update the hash query (?page=2); browser reload and Back/Forward
preserve page selection. Missing/invalid/out-of-range pages use page 1 (API offset
limit 10000). Removed this view's Refresh button; errors ask for browser reload.
Customer orders and other pagination remain unchanged. F10 still awaiting review.
Revision verification: 37 JS unit tests passed; focused real-database browser
test passed (14.0s), including page-2 reload and Back/Forward. Build and whitespace
checks passed. No commit requested for this revision.
F11 accepted; user requested commit and F12. Admin Create restaurant navigation
opens /restaurants/new hash form with name/address and API-aligned length/blank
validation. Authenticated POST /restaurants, busy guard, failure/expiry feedback,
success details and link to new menu. Success invalidates the cached restaurant
list. Per-account form state; navigation discards unsaved values. No backend or
dependency changes. Existing API allows duplicate names and has no idempotency:
uncertain creation advises checking the list before retrying. No automatic retry.
Verification: 41 JS unit tests, all 14 browser tests (36.8s), 2 UI-serving tests
passed. Real DB journey checks validation, creation, menu/reload persistence,
listing and staff UI denial. Existing dependency/color warnings remain.
Compose rebuilt healthy. Stop for F11 review.
F1.1 extracts routeFromHash/viewForRoute into app/ui/routes.js, imported by the
browser and Node tests. app.js now loads as a browser module. Added package.json
with type=module and test:unit; no npm dependencies or application build step.
Node 24.20.0/npm were already installed in the user's normal environment.
Verification: 3 JS unit tests passed; 2 UI-serving tests passed (2 existing
warnings). Local browser smoke verified rendering and navigation after module
conversion. No Docker rebuild or full backend suite needed for this change.
F1.1 accepted; proceeding to the agreed browser integration submilestone F1.2.
Later scopes remain proposals to review one milestone at a time.
Serve same-origin built HTML/assets at /ui/ behind existing Nginx. Vue SFCs with
Vite, minimal CSS, hash navigation, no external CDN at runtime. API client
generation and token persistence remain undecided before affected work.

| Milestone | Scope / acceptance |
|---|---|
| F1 | UI shell served locally and through Nginx; local assets and navigation work. |
| F1.1 | JavaScript unit tests: use Node's built-in test runner/assertions; extract route selection into an importable module, load application JavaScript as a browser module, and test empty, known and unknown hashes. `npm run test:unit` passes without browser, server or database. Document Node setup and ignore generated dependencies. No application build step. |
| F1.2 | Browser integration tests: add Playwright Test with Chromium only and two tests for navigation/Back/Forward and direct hash URL/refresh. `npm run test:browser` starts a temporary local Uvicorn server; allow targeting Compose via configuration. Document setup, ignore reports, and keep tooling out of the production image. No database fixtures needed for the shell. |
| F2 | Restaurant list with pagination, loading, empty and error states. |
| F3 | Selected restaurant menu; unavailable items marked. |
| F4 | Login/logout, current user/role and expired login handling. |
| F5 | Customer registration with validation and success feedback. |
| F6 | One-restaurant cart, quantities and estimated total. |
| F7 | Checkout, delivery details, idempotent retries and confirmation. |
| F8 | Customer order list/detail with explicit refresh. |
| F9 | Staff menu creation/editing/availability for assigned restaurants. |
| F10 | Staff order listing and permitted status transitions. |
| F11 | Admin restaurant creation. |
| F12 | Admin staff creation/assignment; verify API support before implementation. |
| F13 | Review all role journeys through Nginx and document limitations. |

Lifecycle: sessionStorage cart and JWT, explicit refresh for orders, visible
loading/errors and disabled duplicate submissions. Preserve checkout key on an
uncertain outcome; clear cart only after confirmation. Backend enforces roles
and prices. Resolve persistence choices before F4/F6.

## Continuity notes
- User requested lower token usage: use targeted reads and compact check output;
  avoid repeating successful checks without a new reason.
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
- Admin supplies the initial staff password; use existing password rules and hashing.
- Email policy accepted by user: trim, validate format, lowercase; preserve dots
  and plus tags. Apply consistently to registration and future login/recovery.
  PostgreSQL enforces case-insensitive uniqueness with an index on lower(email).
- Order creation must be atomic and idempotent. Persist a customer-scoped key
  and request fingerprint with the order. Repeating the same request returns
  the existing order; reusing the key with a different payload is a conflict.
- User agreed: checkout uses current database price/availability and locks selected
  menu rows until commit. Earlier committed edits are used; later edits wait.
  A retry returns the stored order without repricing, even if the menu changed.
- Order sequence: `pending -> accepted -> out_for_delivery -> delivered`.
- Status updates: next step only; current status returns 200 without a change;
  skipped/backward steps return 409. User requested no explicit row locking.
  Conditional UPDATE checks the observed status; if a competing update wins,
  return 200 if target is current, otherwise 409. No SELECT FOR UPDATE for statuses.
- Use PostgreSQL `NUMERIC` and Python `Decimal` for money and server-calculated
  totals. User selected EUR, positive prices with at most two decimal places;
  API rejects excess precision rather than rounding. Menu prices use NUMERIC(10,2).
- Assigned staff and admins perform restaurant operations. Admins bypass staff
  assignments but still obey resource existence, validation and transition rules.
  Customer-only operations remain customer-only.
- Preserve item-name and unit-price snapshots in orders. Initially manage menu
  changes through edits and availability; no menu deletion endpoint is planned.
- Create files only when their milestones need them.

Implementation proposals recorded for the plan: synchronous SQLAlchemy sessions,
thin HTTP routers, Pydantic request/response schemas, and service functions for
workflows. Start with one models file; avoid a generic repository abstraction.

## Decisions to settle before affected work

- Exact performance and metrics acceptance criteria. The PDF mentions
  p95 below 500 ms, contextual logs without PII, service metrics, and database
  snapshots, but workload and operational expectations are unspecified. Do not
  add tooling without resolving their scope. The user explicitly chose to skip
  backup implementation; database snapshots are a production consideration only.

## Milestones and acceptance criteria

Milestones 1-17 are **accepted**;
Milestones 18-19 are **accepted**;
Milestones 20-21 are **accepted**.
Each is a separate review stop and includes relevant tests or
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
| 21 | Request logging | Logs include request IDs and useful failure context. User revised scope to permit schema-redacted bodies: review annotations/serializer first, then integrate bounded payload logging with tests. |

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

- Milestone 21 redaction step 1: added app/log_redaction.py to_log_dict(BaseModel).
  Sensitive fields use Field(json_schema_extra={"sensitive": True}); passwords,
  tokens, personal names/emails and delivery/default addresses are marked in
  auth, staff, and order schemas. Public restaurant/menu fields and IDs remain visible.
- Serializer traverses declared nested models/lists, masks entire marked fields
  and SecretStr/SecretBytes, encodes Decimal/date values, and omits unstructured
  dicts/arbitrary objects. Model extras excluded; raw dictionary input rejected.
  Normal model/API serialization unchanged. New fields still require sensitivity review.
- Verification: 389 tests passed (9 new), with 2 existing dependency warnings.
  Covers inherited fields, tokens, nested request/response models, no mutation,
  whole-field redaction, unknown extras/dicts and safe value preservation.
- Middleware not integrated with serializer yet; no bodies logged. No migration
  or dependency added; running containers not rebuilt for this helper-only step.
  All milestone 21 changes remain uncommitted; stop for step 1 review.
- Milestone 21: request middleware generates UUID IDs, returns X-Request-ID,
  and writes JSON summaries with method, route template, status, duration_ms.
  Unknown paths omitted. Incoming IDs ignored; no bodies, query strings, raw
  parameter values, auth headers, cookies, IPs, or user details in summaries.
- Unexpected endpoint exceptions return generic 500 and log exception class
  only, without messages/tracebacks. Existing simulated write-failure test now
  asserts safe 500 plus rollback/key reuse instead of a propagated exception.
- Docker/local instructions disable Uvicorn access logs. Nginx access summary
  includes response request ID/status/duration only; server error log disabled
  because raw errors may contain URLs/IPs. Startup checks remain available.
- Verification: 380 tests passed (8 new), with 2 existing dependency warnings.
  Rebuilt/recreated Compose stack healthy; nginx -t passed. Live 200/404/422
  requests had matching app/proxy IDs with synthetic path/query/body/header
  markers absent from both services' logs. No test data written by probes.
- No dependencies or migrations added; head0006. Stack running for review.
  Duration ends when response headers are ready; future streaming/background
  task failures require separate handling. Infrastructure/database logs and
  retention/aggregation are outside this HTTP logging implementation. Reduced
  error detail is intentional; local debugging is needed for full traceback.
  Milestone 21 remains uncommitted; nothing pushed. Open scope questions retained.
- Milestone 20: Compose shares app settings via YAML anchor, connects to db:5432,
  waits for DB health, runs one-off migrations, then starts app and Nginx after
  successful migration/app health. Nginx exposes localhost HTTP_PORT (default8080),
  app has no host port; existing PostgreSQL volume and localhost port retained.
- nginx/default.conf proxies to app:8000; mounted read-only. .env.example includes
  HTTP_PORT. Compose requires nonempty JWT_SECRET, including DB-only commands;
  README initial setup now generates it only when absent/empty.
- Verification: compose config passed; image built; migrate exited 0/head0006;
  db/app/nginx healthy; nginx -t passed. Through Nginx verified HTTP health,
  restaurant DB read, docs/OpenAPI, 401, login, profile, and customer orders.
  Temporary account inserted and deleted by exact ID; no test account retained.
- Stack left running at localhost:8080 for review. No Python changes or new
  dependency/schema migration. No TLS, restart policy, zero-downtime upgrade, or
  production sizing. Nginx resolves app at startup; documented whole-stack restart
  after rebuild preserves volume and refreshes that address. No full Python suite
  rerun for configuration-only changes. Milestone 20 uncommitted; nothing pushed.
- Milestone 19: Dockerfile uses python:3.11-slim, installs the application without
  test extras, includes Alembic/migrations, and runs Uvicorn on 0.0.0.0:8000 as
  appuser UID 10001. Standard-library HTTP health check; no reload. .dockerignore
  allowlists build inputs, excluding .env/.venv/Git/tests and caches.
- Verification: built takeaway-service:milestone19; temporary container became
  healthy; internal and host HTTP /health returned 200/status ok; UID 10001,
  migration presence, absent .env/.venv, and pip check verified. Temporary
  container stopped and auto-removed. Image retained for user review.
- No Python behavior changed; full 372-test suite was not rerun for Docker-only
  changes. No DB connection or Nginx exercised here; full deployment is milestone
  20. No auto-migrations. Base image/dependency ranges are not locked; build
  resolved PyJWT 2.14.0 while the existing local environment used 2.13.0.
- User approved milestone 19 and requested its commit; nothing pushed.
- Milestone 18: assigned-staff PATCH /restaurants/{restaurant_id}/orders/{order_id}/status
  accepts only a status field and returns full OrderResponse (200). Validates
  current/next status; missing or mismatched order 404; invalid transitions 409;
  invalid body/IDs 422. Existing staff dependency enforces current role/assignment.
- Conditional UPDATE includes the observed status and restaurant ID. Zero updated
  rows trigger a refresh: matching target succeeds, otherwise conflict. No explicit
  order-row lock; PostgreSQL still uses normal UPDATE locks. No version column.
- Verification: 372 tests passed (35 new), with 2 existing dependency warnings.
  Includes all 16 current/target pairs, unchanged non-status data, customer readback,
  access restrictions, invalid inputs, simultaneous same-target updates, and
  separate-connection competing changes after read but before write.
- No dependencies or migrations added; head remains 0006. No cancellation,
  notifications, transition history, or custom lock timeout. User approved
  milestone 18 and requested its commit; nothing pushed.
- Milestone 17: GET /restaurants/{restaurant_id}/orders requires current staff
  role and restaurant assignment. Returns all customers' orders for only that
  restaurant, descending ID, with delivery details and purchased item snapshots.
  Pagination: limit 1-100 (default 20), offset 0-10,000 (default 0).
- Moved require_assigned_staff to auth/dependencies.py for menu and order reuse.
  Item rows fetched once per page; existing order response helper accepts those
  prefetched lines. No per-order item query on staff lists. No internal keys returned.
- Verification: 337 tests passed (20 new), with 2 existing dependency warnings.
  Tests cover restaurant isolation, multiple customers, snapshots/status, pagination,
  empty pages, current role/assignment restrictions, and invalid parameters.
- No dependency or migration changes; schema head remains 0006. No status filters,
  total counts, separate staff detail endpoint, or status updates. Pagination has
  no snapshot across requests. User approved milestone 17 and requested its commit.
- Milestone 16: customer-only GET /orders lists summaries scoped to the signed-in
  customer, descending ID, with limit 1-100 (default 20) and offset 0-10,000
  (default 0). GET /orders/{order_id} returns the existing full response including
  delivery details and item snapshots. Missing and other-customer orders both 404.
- Current role checked: staff/admin 403, missing/invalid token 401. Invalid IDs
  and pagination 422. Summary excludes delivery details/items and internal keys.
- Verification: 317 tests passed (24 new), with 2 existing dependency warnings.
  Tests cover isolation, current status/snapshots, pagination and bounds, empty
  pages, missing orders, and current-role changes. New test data rolls back.
- No migration or dependency added; schema head remains 0006. No total counts,
  filters, staff access, or status updates. Offset pages do not preserve a snapshot.
  Milestone 16 remains uncommitted for review; nothing committed or pushed by agent.
- Milestone 15: customer-only POST /orders requires Idempotency-Key (1-128 ASCII
  letters/digits/underscore/hyphen), restaurant ID, explicit delivery name/address,
  and 1-100 distinct item IDs with integer quantities 1-100. No client price/total.
- Service locks customer row before key lookup, then selected menu rows in ID
  order. Computes Decimal total, snapshots item names/prices, creates pending
  EUR order/items and commits together. Any error rolls back. New order returns
  201; same normalized request/key returns existing order (200); different request
  returns 409. Item ordering and trimmed delivery whitespace do not affect hash.
- Missing restaurant returns 404; missing/cross-restaurant items 422; unavailable
  items 409. Failed requests do not retain the key. Role is refreshed under lock.
- Verification: 293 tests passed (43 new), with 2 existing dependency warnings.
  Includes separate-connection overlapping retries/conflicts, both menu-lock
  orderings, rollback after simulated item-write failure, snapshots, key scope,
  authorization, and validation. Concurrency tests commit temporary fixture data
  and delete only those records afterward; other tests roll back.
- No dependencies or migration added; head remains 0006. Requests from the same
  customer are serialized, and overlapping carts can wait on menu locks. No
  custom lock timeout/retry policy. No order read/list endpoints, status updates,
  online payment, or price confirmation flow. Current price can differ from the
  browsing price, as accepted. Milestone 15 uncommitted for review; nothing pushed.
- Milestone 14: Order/OrderItem models and migration 0006. Orders store customer,
  restaurant, delivery-name/address snapshots, status, NUMERIC(18,2) total, EUR,
  creation timestamp, customer-scoped idempotency key (128 chars), and a 64-char
  lowercase hex request fingerprint for the future SHA-256 calculation.
- Items store menu reference, name/unit-price snapshots, and positive quantity;
  one row per order/menu pair. Foreign keys and CHECK/unique constraints enforced.
- Verification: migration applied, alembic check passed; 250 tests passed (38 new)
  with 2 existing dependency warnings. Tests cover snapshots surviving changes,
  key scope, required fields, valid statuses, invalid amounts and references.
  Test rows roll back. No new dependencies or HTTP endpoints.
- Schema alone does not enforce customer role, nonempty orders, item/restaurant
  agreement, total=sum(items), or forward-only transitions. These are workflow
  responsibilities in later milestones. No fingerprint generation or retry
  handling yet. No cascading deletes; downgrade deletes order data and was not
  run on the user's database. User approved milestone 14 and requested its commit.
- Milestone 13: PATCH /restaurants/{restaurant_id}/menu-items/{item_id} updates
  supplied name/price/available fields only. Same validation as creation; empty
  requests, explicit nulls, and extra fields return 422. Returns full item (200).
- Creation and updates share require_assigned_staff in the menu router. Current
  role/assignment required; missing or mismatched item returns 404. Restaurant ID
  and item ID are both used in the lookup, preventing cross-restaurant edits.
- Verification: 212 tests passed (36 new), with 2 existing dependency warnings.
  Tests cover partial updates, public readback, unchanged omitted fields, invalid
  requests without writes, current permissions, mismatched/missing items and IDs.
- No migrations or dependencies added; schema head remains 0005. No deletion or
  optimistic concurrency/version checks; competing edits to the same field may
  overwrite one another. Coordination with order creation remains undecided for
  the order workflow. User approved milestone 13 and requested its commit.
- Milestone 12: public GET /restaurants/{restaurant_id}/menu-items returns only
  that restaurant's items, ordered by ID, including unavailable items. Uses the
  existing response schema (decimal-string EUR price and availability).
- Pagination matches restaurants: limit 1-100 (default 20), offset 0-10,000
  (default 0). Empty pages return []; missing restaurant returns 404; invalid
  IDs/pagination return 422. No total counts or snapshot between pages.
- Verification: 176 tests passed (18 new), with 2 existing dependency warnings.
  Tests cover restaurant isolation, public access, response fields, pagination,
  empty/missing restaurants, and invalid inputs. Test rows roll back.
- No dependencies or migration added; schema head remains 0005. No menu editing
  or detail endpoint added. User approved milestone 12 and requested its commit.
- Milestone 11: POST /restaurants/{restaurant_id}/menu-items requires the current
  staff role and assignment. Creates name, EUR price, and availability (default
  true). Returns 201 with ID/restaurant ID/name/price/available/currency.
- Migration 0005 creates menu_items with restaurant foreign key, required fields,
  NUMERIC(10,2) price and positive/range check. API accepts 0.01-99,999,999.99,
  rejects excess fractional precision, trims names (1-200), rejects extra fields.
  Response prices are decimal strings with two places; currency is fixed EUR.
- Verification: 158 tests passed (36 new), with 2 existing dependency warnings;
  migration applied and alembic check passed. Tests roll back rows. No dependencies
  added. No browsing, editing, or deletion in this milestone.
- Database NUMERIC scale rounds excess precision in direct SQL; API validation
  rejects it before insertion. No concurrent role/assignment mutation API exists;
  authorization checks current state when the request is handled.
- User approved milestone 11 and requested its commit; nothing pushed.
- Milestone 10: admin-only POST /staff accepts email/name/initial password and
  always creates staff. Normalizes email/name and hashes the password; duplicate
  email returns 409 without modifying the existing account. Staff can log in.
- POST /staff/{staff_id}/restaurants/{restaurant_id} creates an assignment (201).
  Missing records return 404, non-staff targets and duplicate pairs return 409,
  invalid IDs return 422. Both endpoints require current admin authorization.
- Migration 0004 adds a composite primary key and foreign keys for assignments.
  Multiple staff per restaurant and multiple restaurants per staff are supported.
  The API checks staff role; foreign keys enforce existence, not user role.
- Verification: migration applied; alembic check passed; 122 tests passed
  (29 new) with 2 existing dependency warnings. Tests roll back their data.
- No dependencies added. No password change/reset, invitation delivery, assignment
  removal, or staff listing included. Admin must communicate the initial password
  outside the API. User approved milestone 10 and requested its commit; no push.
- Milestone 9: public GET /restaurants and GET /restaurants/{restaurant_id}.
  Responses contain ID/name/address. List orders by ascending ID, defaults to
  limit 20/offset 0, bounds limit to 1-100 and offset to 0-10,000. Empty pages
  return []; missing restaurants return 404; invalid parameters return 422.
- Verification: 93 tests passed (17 new), with the existing 2 dependency
  warnings. Tests cover public reads, ordering, pagination, empty pages, and
  invalid/missing IDs. Test data rolls back. No migration or dependency added;
  schema head remains 0003. No menus, search, total counts, or snapshot pagination.
- User approved milestone 9 and requested its commit and milestone 10.
  Staff credential provisioning remains undecided before implementation.
- Milestone 8: Restaurant model and migration 0003; admin-only POST /restaurants;
  shared require_admin dependency; request/response schemas. Returns 201 with
  ID/name/address. API trims text; name 1-200, address 1-1000; rejects extra fields.
- Names are not unique (branches may share a name). Database requires both fields.
  No browsing, assignments, editing, deletion, or new dependencies added.
- Verification: migration applied, alembic check reports no schema drift;
  76 tests passed (14 new) with existing 2 dependency warnings. Tests cover
  persistence, normalization, non-admin/missing/invalid authentication, updated
  database roles, and invalid input without writes. Test rows are rolled back.
- User approved milestone 8 and requested its commit. No push requested.
- Milestone 7: added `python -m app.create_admin --email ... --name ...` with
  hidden password and confirmation prompts. Reuses registration validation and
  Argon2 hashing, assigns admin explicitly, commits only a new account. Duplicate
  email errors never promote or overwrite existing users, regardless of role.
- Controlled validation, duplicate, database, and cancelled-input errors exit 1;
  success prints only the new ID and exits 0. No password argument; visible-input
  fallback is refused. Access is through a trusted terminal/database environment.
- Verification: 62 tests passed (9 new), with existing 2 dependency warnings;
  module `--help` works. New tests cover command success and admin login, duplicate
  emails for all roles, invalid input before opening the DB, and hidden-input
  failure. Tests roll back accounts; no permanent admin was created.
- No dependencies, migration, HTTP endpoint, or account-promotion feature added.
  Distinct emails can provision multiple admins. User requested milestone 7 commit;
  no push requested.
- Milestone 6: JSON POST /auth/login for every role; HS256 access tokens with
  sub/iat/exp, configurable 30-minute expiry; bearer-protected GET /users/me.
  Current user is read from PostgreSQL; credentials and hashes are not returned.
- Added PyJWT 2.13.0. Required private JWT_SECRET in separate AuthSettings;
  generated local ignored `.env` key without exposing it or replacing a supplied
  nonempty key. Tests override the key. No migration required; head remains 0002.
- Shared email normalization between registration/login. Wrong-password and
  unknown-email responses are identical 401s; missing users still incur hash
  verification. Tokens require the fixed algorithm and all three claims, and
  reject malformed/out-of-range user IDs before querying PostgreSQL.
- Preserved the repository's existing 8-character registration minimum, which
  was present at milestone 6 start; updated stale README wording. Login accepts
  1-128 characters and verifies exact password input.
- Reused the rollback/savepoint API fixture via tests/conftest.py. New tests
  cover all roles, case/whitespace normalization, safe profile responses, expiry,
  wrong signature/algorithm, missing claims, malformed subjects, missing bearer,
  changed/deleted users, invalid input, and indistinguishable credential errors.
- No refresh tokens, token revocation/logout, rate limiting, or onboarding added.
  User approved milestone 6 and requested its commit; no push requested.
- Milestone 6 verification: 53 tests passed with only the existing 2 dependency
  warnings; pip check passed; signing/verification with local JWT settings passed
  without printing tokens or keys. Automated tests leave no accounts behind.
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
