# Takeaway Service

A take-home backend built one small milestone at a time. Exposes customer
registration at `POST /auth/register`, login at `POST /auth/login`, and the
protected profile at `GET /users/me`, and admin-only `POST /restaurants`.
Public restaurant browsing uses `GET /restaurants` and `GET /restaurants/{id}`.
`GET /health` returns HTTP 200 with
`{"status":"ok"}` and checks application liveness, not database readiness.

## Setup (Windows PowerShell)

Requires Python 3.11 or newer. Run commands from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

The virtual environment isolates this project's dependencies. The editable
install (`-e`) makes source changes available without reinstalling the project;
`[test]` includes pytest and HTTPX. Calling the environment's Python directly
avoids needing to activate it or change PowerShell execution policy.

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --no-access-log
```

Uvicorn serves the FastAPI application: `app.main:app` means the `app` object in
`app/main.py`. `--reload` restarts it after source edits during development.
Stop it with Ctrl+C.

In another PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected result: `status` is `ok`. Interactive API documentation is available at
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Test

Start PostgreSQL and apply migrations before running all tests (see below).

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The health test checks the HTTP status and JSON body through FastAPI's
`TestClient`; no running server is needed. See the
[FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/).

## Local PostgreSQL

Requires Docker Desktop running with Linux containers (or an equivalent Docker
Engine with Compose). Verify `docker compose version` and `docker info` work.
Database sessions and Alembic use this database; the health endpoint remains
independent of it.

If Docker reports that the `docker_engine` pipe is missing, start Docker Desktop
and select its Linux context before running the commands below:

```powershell
docker desktop start
docker context use desktop-linux
docker info
```

The context selects which engine receives Docker commands. Alternatively, use
`docker --context desktop-linux compose ...` for an individual command.
After installing Desktop, reopen your terminal so it picks up PATH changes. If
an older terminal cannot find `docker-credential-desktop`, this per-user install
can be added to that terminal's PATH:

```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin;" + $env:PATH
```

Create the local configuration once; keep an existing `.env` if you have one:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -c "import secrets; from dotenv import dotenv_values, set_key; values = dotenv_values('.env'); values.get('JWT_SECRET') or set_key('.env', 'JWT_SECRET', secrets.token_urlsafe(48))"
docker compose config --quiet
docker compose up -d --wait db
docker compose ps
```

Expected: `db` reports healthy. The first startup downloads the PostgreSQL image.
The key-generation command preserves an existing nonempty JWT_SECRET and does
not print it. The full Compose file requires this key even for DB-only commands.
Compose reads `.env` for the database name, user, password, and host port. The
example credentials are for local development only; `.env` is ignored by Git.
The port is bound to `127.0.0.1`, so it is accessible only from this computer.
If port 5432 is occupied, change `POSTGRES_PORT` in `.env`.

We use `postgres:17` to stay on one major version while allowing patch updates.
A named volume, `postgres_data`, stores database files independently of the
container. The health check uses `pg_isready` to check whether PostgreSQL is
accepting connections; it does not verify application schemas or credentials.
The `$$` in the health-check command lets the container expand its variables.

Run a query using the container's database client:

```powershell
docker compose exec db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;"'
```

Expected: one row containing `1`. The shell expands the user/database values
inside the container, so this also works if you edited `.env`.

### Verify persistence

Create a small probe table separate from application tables:

```powershell
docker compose exec db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE TABLE milestone2_probe (id integer PRIMARY KEY); INSERT INTO milestone2_probe VALUES (1);"'
docker compose down
docker compose up -d --wait db
docker compose exec db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id FROM milestone2_probe;"'
```

Expected: the row containing `1` survives container removal and recreation.
After verifying it, remove only the probe table:

```powershell
docker compose exec db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP TABLE milestone2_probe;"'
```

Stop the local database with `docker compose down`. This preserves the volume;
adding `--volumes` would delete its data. Initial database/user/password settings
apply only when the volume is empty; editing `.env` does not update credentials
in an existing database. The bootstrap user is a database superuser for this
local setup, not a production application account. See the
[official PostgreSQL image documentation](https://hub.docker.com/_/postgres).

## Database sessions and migrations

After updating the code, install the added dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

`app/config.py` reads the same `POSTGRES_*` values as Compose from `.env`.
Environment variables take precedence. Python defaults `POSTGRES_HOST` to
`127.0.0.1`, so an existing milestone 2 `.env` still works. Run Python and Alembic
commands from the project root so they find `.env`. Restart Python processes
after configuration changes.

Pydantic Settings validates configuration. SQLAlchemy builds the connection URL
from separate values, so special characters in passwords do not need manual URL
encoding. Psycopg is the PostgreSQL driver; its binary package avoids local
compiler setup on Windows.

`app/db.py` creates one cached engine (a connection pool) when first needed.
`get_session` provides a session for FastAPI dependencies. The `with`
block closes it even when a request fails, rolling back unfinished work. Features
must commit successful writes explicitly. Registration uses this session.
See [SQLAlchemy session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html).

With PostgreSQL running, apply migrations before running database tests:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest -q -m integration
```

Expected: `366 passed, 35 deselected`. Tests check connectivity, user-table
constraints, registration, authentication, admin provisioning, and restaurants.
Most tests insert rows inside transactions and roll them back after
each test. Order concurrency tests commit temporary records across connections
and delete only their own records afterward. The default `pytest -q` command runs all tests, including integration
tests. VS Code can also discover and run individual tests without a marker override:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: `401 passed` when PostgreSQL is running and migrations are applied.
To run only tests that do not need Docker, use
`python -m pytest -q -m "not integration"` with the virtual environment's Python.
Registration tests use an outer transaction and session savepoints, so endpoint
commits can be exercised without leaving test accounts in the database.

Alembic records ordered schema changes as revision files in `migrations/versions`.
It shares the application's settings and engine; credentials are not stored in
`alembic.ini`. Verify that it connects:

```powershell
.\.venv\Scripts\python.exe -m alembic current -v
```

Expected: revision `0006 (head)` after upgrading. `upgrade head` applies pending
migrations; running it again does not recreate the table. `alembic check` compares
the database schema with the model and should report no new upgrade operations.
`app.models` is imported in the migration environment to register model metadata.
See the [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## User model

`app/models.py` defines how a Python `User` maps to a row in `users`.
Migration `0001` creates the actual table; defining a model alone does not create
tables. The database assigns integer IDs and enforces unique emails, non-null
email/password hash/role/name, and roles limited to `customer`, `staff`, `admin`.
`default_address` is optional. The role must be supplied explicitly.

A CHECK constraint validates the role even for SQL written outside the app.
Migration `0002` replaces the exact-email unique constraint with a unique index
on `lower(email)`. This prevents capitalization variants even for direct database
writes, without changing existing addresses. If existing rows conflict, the
migration fails transactionally rather than deleting or merging accounts.
Required text columns reject NULL; registration also rejects empty names.

The migration includes a downgrade that drops `users`, which would delete user
data. Do not use downgrade on data you need to keep.

## Customer registration

Start PostgreSQL, apply migrations, and run Uvicorn using the commands above.
In [the API docs](http://127.0.0.1:8000/docs), open `POST /auth/register` and try:

```json
{
  "email": "Alice.Smith+takeaway@example.com",
  "password": "a long example passphrase",
  "name": "Alice Smith",
  "default_address": "12 Example Street"
}
```

This creates a real local customer. A successful response is HTTP 201 with the
ID, normalized email, name, role `customer`, and address. No password, hash, or
token is returned. The address may be omitted or null. Sending the same email
again, including capitalization variants, returns HTTP 409.

Rules:
- Trim surrounding email whitespace, validate its format, then lowercase it.
  Preserve dots and `+tags`; do not apply Gmail-specific alias rules.
- Passwords are 8-128 characters and are never trimmed. No special-character
  composition rules are imposed. Hashing uses Argon2id via `pwdlib`, with a fresh
  salt for each password. See [FastAPI's hashing guide](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).
- Names are trimmed and must be 1-200 characters; supplied addresses are trimmed
  and must be 1-1,000 characters.
- Unknown fields, including `role` and `password_hash`, return HTTP 422. The
  server always assigns the customer role.
- Validation errors return locations, messages, and error types, excluding raw
  input values to avoid echoing passwords.

`app/auth/schemas.py` validates requests and limits response fields;
`service.py` hashes and inserts the customer, then commits. The unique database
index decides duplicate conflicts, including competing inserts; only that
specific violation is translated into HTTP 409. `router.py` maps this outcome
to HTTP. Other database errors are not mislabeled as duplicate emails.

Email format validation does not verify mailbox ownership. Verification emails
are not implemented. Login uses the same email normalization policy.

## Login and current user

Login requires a private `JWT_SECRET` of at least 32 characters in `.env`.
A key has already been generated for this workspace. On a fresh setup, after
copying `.env.example`, generate it once (the command writes it without printing):

```powershell
.\.venv\Scripts\python.exe -c "import secrets; from dotenv import set_key; set_key('.env', 'JWT_SECRET', secrets.token_urlsafe(48))"
```

Keep that file local. Rerunning the command replaces the key, invalidating
previously issued tokens. `ACCESS_TOKEN_MINUTES` defaults to 30 and accepts
1-1440 minutes. Restart Uvicorn after configuration changes. Database settings
and JWT settings are separate so migration commands do not require a signing key.

After registering a customer, use its credentials to log in:

```powershell
$body = @{
    email = 'alice.smith+takeaway@example.com'
    password = 'a long example passphrase'
} | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -ContentType 'application/json' -Body $body
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod http://127.0.0.1:8000/users/me -Headers $headers
```

Login returns HTTP 200 with `access_token` and `token_type: bearer`. The profile
returns the authenticated user's ID, email, name, role, and optional address.
It never includes the password hash. In `/docs`, execute `/auth/login`, copy only
the access token into **Authorize**, and then execute `/users/me`.

All three roles use the same login route. Public registration still creates
customers only; initial admins use the command below and admins create staff
through `POST /staff`. Login
checks the password exactly as supplied (1-128 characters), rather than applying
the registration minimum to existing passwords. Invalid credentials return the
same HTTP 401 message for an unknown email or wrong password. Unknown emails
still perform a dummy hash verification to avoid an immediate early return.

JWTs contain the user ID (`sub`), issue time (`iat`), and expiry (`exp`). They are
signed with HS256, not encrypted, so no personal data is placed in the token.
Decoding fixes the allowed algorithm and requires all three claims; malformed,
expired, wrongly signed tokens and tokens for deleted users return HTTP 401.
`/users/me` reads the current user from PostgreSQL on each request. See
[PyJWT's documentation](https://pyjwt.readthedocs.io/en/stable/usage.html).

No refresh tokens, logout/revocation mechanism, or rate limiting are included.
An access token remains usable until it expires, the signing key changes, or
the user is deleted. Automated login tests use their own key and roll back data.

## Initial admin provisioning

From a trusted local PowerShell terminal, with PostgreSQL running and migrations
applied:

```powershell
.\.venv\Scripts\python.exe -m app.create_admin --email admin@example.com --name "Local Admin"
```

Enter a password and confirm it when prompted. Input is hidden; the command has
no password argument. It refuses to fall back to visible input if the terminal
cannot hide it. Use VS Code's terminal rather than its Debug Console.

The command reuses registration's email/name/password validation and Argon2
hashing, but assigns `admin` internally. It prints the created ID and exits with
code 0 on success. The account can then log in at `/auth/login`. This is a real
database write; no permanent admin was created during automated verification.

An existing email, including capitalization variants, causes a controlled error
and exit code 1. The existing account's role, name, and password are preserved.
There is no promotion, password reset, or public admin registration endpoint.
The command can provision another admin with a different email; it is restricted
by access to this trusted environment and its database credentials, not by an
HTTP login. No new dependencies or schema migration are needed.

To test this milestone alone:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_create_admin.py -q
```

Expected: `9 passed`. Database tests roll back their admin accounts afterward.

## Restaurant creation

Apply migration `0003` with `python -m alembic upgrade head` using the virtual
environment. It creates `restaurants` with an integer ID, required name, and
required address. Names need not be unique because branches can share a name.

Create an admin using the command above, log in, and authorize in `/docs`.
Then execute `POST /restaurants` with:

```json
{
  "name": "Test Kitchen",
  "address": "12 Example Street"
}
```

Expected: HTTP 201 with the generated `id`, `name`, and `address`. This persists
a real restaurant. Names and addresses are trimmed and must contain 1-200 and
1-1,000 characters respectively. Missing, blank, oversized, or extra fields
return HTTP 422. IDs are assigned by PostgreSQL, not accepted from the client.

Missing/invalid authentication returns 401. Authenticated customers and staff
receive 403. `require_admin` checks the current database role on each request.
Authentication establishes who the user is; authorization checks whether that
user may perform this action. The route performs one insert and commit, so it
does not need a separate service layer yet.

Run the milestone's tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_restaurants.py -q
```

Expected: `14 passed`. Tests roll back their data. Staff assignment, editing,
and deletion are not included in this milestone.

## Restaurant browsing

With PostgreSQL and Uvicorn running, no login is needed:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/restaurants?limit=20&offset=0'
Invoke-RestMethod http://127.0.0.1:8000/restaurants/1
```

The list returns a JSON array of restaurants containing `id`, `name`, and
`address`, ordered by ascending ID. `limit` defaults to 20 and accepts 1-100;
`offset` defaults to 0 and accepts 0-10,000. Offset means how many rows to skip.
An empty database or a page beyond available rows returns `[]`. Invalid
pagination values return HTTP 422.

The detail endpoint returns one restaurant, or HTTP 404 with
`{"detail":"Restaurant not found"}` if the ID does not exist. Replace `1` above
with an ID from your list. IDs outside the positive PostgreSQL integer range
return HTTP 422.

Pagination does not include a total count or preserve a snapshot between
requests; changes to the restaurant list can shift later pages. Menus and search
are not included. No new migration or dependency is needed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_restaurant_browsing.py -q
```

Expected: `17 passed`. Tests cover public access, ordering, pagination bounds,
empty pages, detail responses, and invalid or missing IDs. Test rows roll back.

## Staff onboarding and assignment

Apply migration `0004` with the virtual environment's Python:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Log in as an admin and authorize in `/docs`. Execute `POST /staff` with:

```json
{
  "email": "staff@example.com",
  "name": "Kitchen Staff",
  "password": "a long initial passphrase"
}
```

Expected: 201 with the new user's ID, normalized email/name, role `staff`, and
null default address. The password is hashed and never returned. The admin
supplies and communicates this initial password; the staff member uses it at
`POST /auth/login`. There is no invitation or password-change flow yet.

Email and password rules match registration. Extra fields (including `role`)
are rejected with 422. Existing emails return 409 without changing that account.

Use the returned ID and an existing restaurant ID with
`POST /staff/{staff_id}/restaurants/{restaurant_id}` (no request body).
Expected: 201 with `staff_id` and `restaurant_id`. Each staff member may have
multiple restaurants, and each restaurant may have multiple staff. A composite
primary key makes each pair unique, so repeating an assignment returns 409.
Foreign keys ensure both referenced records exist; the API checks the staff role.

Missing records return 404, assigning a customer or admin returns 409, and
invalid IDs return 422. Both endpoints return 401 without valid authentication
and 403 for customers/staff. Assignment removal and staff listing are not included.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_staff.py -q
```

Expected: `29 passed`. PostgreSQL must be running. Tests cover creation/login,
password hashing, duplicate emails, authorization, validation, assignments, and
database constraints. Test rows are rolled back.

## Menu item creation

Apply migration `0005` with the virtual environment's Python:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Create a staff account and assign it to a restaurant as described above. Log in
as that staff member and authorize in `/docs`. Execute
`POST /restaurants/{restaurant_id}/menu-items` with the assigned restaurant ID:

```json
{
  "name": "Tomato soup",
  "price": "6.50",
  "available": true
}
```

Expected: 201 with `id`, `restaurant_id`, trimmed `name`, `price: "6.50"`,
`available: true`, and `currency: "EUR"`. This creates a real local menu item.
Availability defaults to true if omitted and accepts JSON booleans only.

Prices must be positive and at most 99,999,999.99 EUR, with at most two decimal
places. Send prices as decimal strings to preserve their exact value; JSON
numbers are also accepted. Python Decimal and PostgreSQL NUMERIC(10,2) store
decimal values exactly. The API rejects excess fractional precision instead of
rounding; direct SQL writes to NUMERIC can still round to its declared scale.
Trailing zeros do not change the price's precision (for example, 6.500 is 6.50).

Names must contain 1-200 characters after trimming. Invalid prices, names, IDs,
or extra fields return 422. The restaurant ID comes from the URL; currency is
fixed by the platform. Missing/invalid authentication returns 401. Customers,
admins, and staff without an assignment receive 403. A staff request for a
missing restaurant returns 404. Role and assignment are checked on each request.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_menu_creation.py -q
```

Expected: `36 passed`, with PostgreSQL running. Tests roll back their data.
Assigned staff can edit menu items using the endpoint below.

## Menu browsing

With PostgreSQL and Uvicorn running, replace `1` with an existing restaurant ID:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/restaurants/1/menu-items?limit=20&offset=0'
```

No login is needed. The response is an array of that restaurant's items, ordered
by ascending item ID. Each item includes `id`, `restaurant_id`, `name`, `price`
as a decimal string, `currency: "EUR"`, and `available`. Unavailable items remain
visible with `available: false`.

Pagination matches restaurant browsing: `limit` defaults to 20 (range 1-100),
and `offset` defaults to 0 (range 0-10,000). Empty menus and pages beyond the
available rows return `[]`. A missing restaurant returns 404; invalid parameters
return 422. There is no total count or snapshot preserved between requests.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_menu_browsing.py -q
```

Expected: `18 passed`. Tests roll back their data. No new migration or dependency
is required for this milestone.

## Menu updates

Log in as staff assigned to the restaurant. In `/docs`, execute
`PATCH /restaurants/{restaurant_id}/menu-items/{item_id}` using IDs from the
public menu. Supply only fields you want to change, for example:

```json
{
  "price": "7.25",
  "available": false
}
```

Expected: 200 with the complete updated item. Its name stays unchanged.
`name`, `price`, and `available` follow the creation rules. Omitted fields retain
their values; an empty object, explicit null, or extra field returns 422.
An invalid field rejects the whole request without applying other changes.

Both creation and updates use the same current-role and assignment check.
Customers/admins/unassigned staff receive 403; missing/invalid authentication
returns 401. A missing item or an item belonging to another restaurant returns
404 after authorization. Invalid IDs return 422. The restaurant cannot be
changed through this endpoint. Updated items appear in public menu browsing.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_menu_updates.py -q
```

Expected: `36 passed`, with PostgreSQL running. Tests roll back their data.
No migration or dependency changes are needed. There is no deletion endpoint
or version check for competing edits; updates to the same field can overwrite
one another. Order creation locks selected menu rows until its transaction finishes.

## Order persistence

Milestone 14 adds database tables only. Apply the migration and run its tests:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest tests/test_orders.py -q
```

Expected: revision `0006` applied and `38 passed`. PostgreSQL must be running.
These persistence tests roll back all inserted rows.

`orders` stores the customer and restaurant IDs, delivery name/address, status,
EUR total, and a timezone-aware creation timestamp. Total uses NUMERIC(18,2)
to allow sums larger than one item's NUMERIC(10,2) price. `order_items` stores
the menu-item reference, purchased name/unit price, and quantity. These copies
are snapshots: later menu or customer-profile changes do not alter old orders.
Each menu item has at most one line per order; quantity represents multiple units.

The idempotency key (up to 128 characters) is unique per customer, so different
customers may use the same key. A 64-character lowercase hexadecimal fingerprint
stores the SHA-256 digest of the normalized request. The creation service below
computes it and handles duplicate requests; the schema alone does not implement retries.

Constraints reject invalid statuses, nonpositive amounts/quantities, blank
delivery details, missing references, and non-EUR currency. Workflow checks for
customer role, a nonempty order, matching restaurant items, and calculated totals
are performed by order creation. Forward status transitions are enforced by the status endpoint below. Foreign keys
prevent deleting referenced records; no cascading deletion is configured.
Downgrading this migration deletes order tables and their data.

## Order creation

Log in as a customer and authorize in `/docs`. Execute `POST /orders` with a new
`Idempotency-Key` header (for example, a UUID) and the following body, replacing
restaurant and item IDs with IDs from your menu:

```json
{
  "restaurant_id": 1,
  "delivery_name": "Alice",
  "delivery_address": "12 Example Street",
  "items": [
    {"menu_item_id": 1, "quantity": 2}
  ]
}
```

Expected: 201 with the order ID, restaurant, delivery details, pending status,
EUR total, creation time, and purchased item snapshots. This creates a real
local order. All prices are decimal strings in the response. Payment remains
on delivery; no payment processing occurs.

Supply delivery details explicitly; the profile's default address is not copied
automatically. Names/addresses are trimmed with the same 200/1,000-character
limits used elsewhere. Include 1-100 distinct menu items, each with an integer
quantity from 1-100. Unknown fields, including prices, totals, customer ID, and
status, are rejected. The server verifies restaurant membership and availability,
calculates the total, and saves the order and all lines in one transaction.

The key accepts 1-128 ASCII letters, digits, underscores, or hyphens. Keep the
same key and body when retrying a request whose result is uncertain:

- Same customer/key/request: 200 with the existing order; no second purchase.
- Same customer/key with a different request: 409 conflict.
- New key: a new purchase, even for the same body.
- Failed validation or transaction: no order or key reservation remains.

The request fingerprint includes normalized delivery details, restaurant, and
item IDs/quantities. Reordering item lines or trimming delivery whitespace does
not change it. Retries use stored prices even after menu prices or availability
change. Keys are scoped to the authenticated customer and retained with the order.

Checkout uses current database prices, which can differ from the browsing price.
The service locks the customer row to serialize that customer's requests, then
locks menu rows in ID order. A staff edit that finishes first is reflected in
checkout; an edit after checkout takes the lock waits until the order finishes.
These are database transaction locks, released on commit or rollback.

Missing/invalid authentication returns 401; staff/admins receive 403. A missing
restaurant returns 404; missing or cross-restaurant items return 422; unavailable
items return 409. Assigned staff update status through the endpoint below.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_order_creation.py tests/test_order_concurrency.py -q
```

Expected: `46 passed`, with PostgreSQL running and migration 0006 applied (includes
the three status-concurrency tests added in milestone 18).
Concurrency tests use separate connections and observe actual PostgreSQL lock
waits. They commit temporary test records, then clean up only those records.
Other order-creation tests roll back their data. No new dependency or migration
is required. Requests can wait on locks; no custom lock timeout is configured.

## Customer order retrieval

Log in as a customer and authorize in `/docs`:

- `GET /orders?limit=20&offset=0` lists only your orders, newest ID first. Each
  summary includes `id`, `restaurant_id`, `status`, `total`, `currency`, and
  `created_at`. Delivery details and item lines are returned by the detail route.
- `GET /orders/{order_id}` returns your order with delivery details and purchased
  item snapshots, using the same response format as creation. Later menu changes
  do not alter the purchased names/prices; status reflects the stored order status.

Pagination uses limit 1-100 (default 20) and offset 0-10,000 (default 0). Empty
history or a page beyond available orders returns `[]`. There is no total count
or snapshot between requests; newly created orders can shift subsequent pages.

A missing order or another customer's order returns the same 404 response:
`{"detail":"Order not found"}`. Missing/invalid authentication returns 401;
staff and admins receive 403. The current database role is checked on each request.
Invalid order IDs or pagination values return 422. Internal idempotency keys and
request fingerprints are never included in these responses.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_order_retrieval.py -q
```

Expected: `24 passed`, with PostgreSQL running. Tests roll back their data.
No new migration or dependency is needed.

## Staff order listing

Log in as staff assigned to a restaurant and authorize in `/docs`. Execute
`GET /restaurants/{restaurant_id}/orders?limit=20&offset=0` with that restaurant ID.

Expected: 200 with a JSON array of that restaurant's orders from all customers,
newest ID first. Each order includes delivery name/address, current status,
EUR total, creation time, and purchased item snapshots. Internal idempotency keys
and fingerprints are excluded. Item lines are fetched in one batch for the page.

The current staff role and assignment are checked using the same dependency as
menu writes. Missing/invalid authentication returns 401; customers, admins, and
staff without an assignment receive 403. A staff request for a missing restaurant
returns 404. An existing assigned restaurant with no orders returns `[]`.

Pagination uses limit 1-100 (default 20) and offset 0-10,000 (default 0). Invalid
IDs or pagination return 422. There are no status filters, total counts, or
snapshot across pages. Assigned staff can update status as described below.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_staff_orders.py -q
```

Expected: `20 passed`, with PostgreSQL running. New tests roll back their data.
No new dependencies or migrations are needed.

## Order status updates

Log in as assigned staff and authorize in `/docs`. Execute
`PATCH /restaurants/{restaurant_id}/orders/{order_id}/status` with:

```json
{"status": "accepted"}
```

The sequence is `pending -> accepted -> out_for_delivery -> delivered`.
Only one step forward is allowed. Requesting the current status returns 200
without changing it; skipped steps or backward moves return 409. A successful
response includes the full order. Customers see the new status through their
order retrieval endpoints. No cancellation or transition-history feature is included.

The service reads the status and issues a conditional UPDATE that succeeds only
if the status still matches that read. It uses no SELECT FOR UPDATE. If another
request wins, the service rereads the order: the same target status returns 200;
a different status returns 409 so the caller can reload. PostgreSQL still takes
its ordinary row lock when executing UPDATE. A delayed retry for a status the
order has already passed returns 409, rather than moving it backward.

Only the current assigned staff role is permitted. Missing/invalid authentication
returns 401; customers/admins/unassigned staff receive 403. Missing or mismatched
orders return 404. Unknown statuses, extra fields, and invalid IDs return 422.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_order_status.py tests/test_order_concurrency.py -k status -q
```

Expected: `35 passed, 5 deselected`. PostgreSQL must be running. Ordinary tests
roll back their rows; concurrency tests commit temporary data and clean up only
their own records. No new dependencies or migrations are needed.

## Application container

With Docker Desktop running, build the application image from the project root:

```powershell
docker --context desktop-linux build -t takeaway-service:milestone19 .
docker --context desktop-linux run --rm --name takeaway-app -p 127.0.0.1:8001:8000 takeaway-service:milestone19
```

The second command runs in the foreground. In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
docker --context desktop-linux inspect --format '{{.State.Health.Status}}' takeaway-app
```

Expected: `status` is `ok`; Docker reports `healthy` after its first successful
check (allow around 10 seconds). API docs are at http://127.0.0.1:8001/docs.
Stop with Ctrl+C in the first terminal, or `docker --context desktop-linux stop
takeaway-app` in the second. `--rm` removes the stopped container, not its image.
If port 8001 is occupied, choose another host port before `:8000`.

The image uses Python 3.11 slim, installs production dependencies from
`pyproject.toml`, and runs one Uvicorn process as non-root UID 10001. Uvicorn
binds all container interfaces so the published localhost port can reach it.
`EXPOSE 8000` documents the container port; `-p` publishes it on the host.
No development reload or test dependencies are included. A Python standard-library
HTTP probe checks liveness without installing curl.

`.dockerignore` only permits application build inputs; local secrets, the virtual
environment, Git history, tests, and caches are excluded. Alembic configuration
and migrations are included, but startup does not run migrations automatically.

This command demonstrates application startup and health without database
configuration. Database-backed endpoints require runtime database settings and
JWT authentication requires JWT_SECRET; those are wired through Compose below.
Container localhost refers to the container itself. The health
endpoint does not verify database readiness.

Verification performed: image build, Docker health status, HTTP health from both
inside and outside the container, non-root UID, migration files, absence of local
secrets/virtual environment, and `pip check`. The temporary test container was
removed afterward. Image tags and dependency ranges are not locked, so future
builds can resolve newer patch/minor versions.

## Full Compose deployment

Ensure `.env` contains the database settings and private JWT_SECRET described
above. If the terminal cannot find `docker-credential-desktop`, add its directory
to PATH before building. Run from the repository root:

```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin;" + $env:PATH
docker --context desktop-linux compose config --quiet
docker --context desktop-linux compose up -d --build --wait
docker --context desktop-linux compose ps -a
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-RestMethod http://127.0.0.1:8080/restaurants
```

Expected: `db`, `app`, and `nginx` are healthy; `migrate` exited with code 0.
Health returns `status: ok`; restaurants returns the current database list.
Open http://127.0.0.1:8080/docs to register/log in and try the existing endpoints.
These requests use the real local database.

Compose starts services in this order:

1. PostgreSQL becomes healthy, using the existing named volume.
2. The one-off `migrate` service runs `alembic upgrade head` and exits.
3. The application starts after migration success and becomes healthy.
4. Nginx starts and proxies requests to `app:8000`.

`x-app` and its YAML anchor share the image/build and environment between the
app and migration service. Within Compose, PostgreSQL is reached at `db:5432`,
regardless of the host-side POSTGRES_HOST/POSTGRES_PORT values. Secrets are passed
at runtime, not copied into the image. Migration failure prevents dependent
services from starting on initial deployment; inspect `compose logs migrate`.

Nginx publishes localhost port 8080 by default; set HTTP_PORT in `.env` to change
it. Uvicorn has no published host port. PostgreSQL retains its localhost port for
Python development and tests. Nginx mounts `nginx/default.conf` read-only and
preserves the request host and authorization header when proxying. This is local
HTTP deployment; TLS and public internet hosting are not configured.

Useful checks:

```powershell
docker --context desktop-linux compose exec nginx nginx -t
docker --context desktop-linux compose exec app python -m alembic current
docker --context desktop-linux compose logs --tail 50 app nginx migrate
```

Expected migration: `0006 (head)`. Health checks indicate liveness; the public
restaurant request also verifies application-to-database connectivity.

For a clean local restart or after rebuilding changed code, use:

```powershell
docker --context desktop-linux compose down
docker --context desktop-linux compose up -d --build --wait
```

`down` preserves the database volume. Do not add `--volumes` for data you want
to retain. Restarting the whole stack also lets Nginx resolve the app's current
container address. No automatic restart policy or zero-downtime upgrade is
configured. `migrate` reruns safely against an already-current schema.

Verified through Nginx: health, database-backed browsing, docs/OpenAPI, unauthorized
access rejection, login, profile, and customer order listing. The temporary test
account was deleted afterward. The stack is left running for review.

## Request logging

Every application HTTP response receives a generated `X-Request-ID`. Incoming
request IDs are ignored, preventing client-supplied personal data from entering
logs. The app writes one JSON request summary to stderr, for example:

```json
{"request_id":"a-generated-uuid","method":"GET","route":"/orders/{order_id}","status":200,"duration_ms":4.12}
```

Route templates replace actual path values; unmatched URLs use `<unmatched>`.
Query strings, raw bodies, headers, cookies, and client IPs are excluded.
Schema-backed routes add redacted payloads as described below.
Duration measures application handling until response
headers are ready, not full network transmission. Entries use INFO for success,
WARNING for 4xx, and ERROR for 5xx.

Unexpected application exceptions return `{"detail":"Internal server error"}`
with status 500 and a request ID. The summary includes the exception class, such
as `RuntimeError`, without its message or traceback, since those may contain SQL
parameters or credentials. This limits diagnosis detail; use local debugging to
investigate the matching code. The middleware covers the current JSON endpoints,
not failures in a future streaming response or background task.

Run local Uvicorn with `--no-access-log` as shown above. The Docker command already
includes it, avoiding duplicate raw URL/IP access logs. Nginx writes a minimal
JSON access summary with status, duration, and the app's response request ID;
it does not log request paths, headers, or client addresses. Its server error
log is disabled because raw error messages can contain those values. Requests
rejected before reaching the app can have an empty Nginx request ID. Startup
configuration checks remain available via `nginx -t`.

```powershell
docker --context desktop-linux compose logs --tail 30 app nginx
.\.venv\Scripts\python.exe -m pytest tests/test_request_logging.py -q
```

Expected: `8 passed`; these logging tests do not require PostgreSQL. They check
ID matching/uniqueness, errors and validation, path/query/header/body exclusion,
and concurrent requests. Database/infrastructure logs are separate from these
HTTP summaries; this milestone does not configure log retention or aggregation.
The rebuilt Compose stack was also checked with synthetic private values: app
and Nginx logs shared response IDs and omitted those values for 200, 404, and
422 requests. The stack remains running for review.

## Schema redaction

Sensitive schema fields now declare metadata, for example:

```python
access_token: str = Field(json_schema_extra={"sensitive": True})
```

`app.log_redaction.to_log_dict(model)` builds a separate representation for logs:

```python
from app.auth.schemas import TokenResponse
from app.log_redaction import to_log_dict

response = TokenResponse(access_token="example-token")
to_log_dict(response)
# {"access_token": "[REDACTED]", "token_type": "bearer"}
```

This does not change the original object or normal API serialization. The metadata
alone does not redact anything; code must call this helper when producing logs.
`PayloadLoggingRoute` connects this helper to the existing request summary,
adding `request_body` and `response_body` using each route's declared schemas.

The helper follows declared fields through nested models and lists, replaces
marked values with `[REDACTED]`, and also masks Pydantic secret types. Decimal
values become strings and dates use ISO format. Extra fields are excluded;
unstructured dictionaries and unsupported objects become `[OMITTED]`. Top-level
input must be a Pydantic model, not raw JSON or a dictionary.

Personal names, delivery/default addresses, passwords, and tokens are marked.
Emails intentionally remain visible, as requested. Public restaurant/menu names,
restaurant addresses, and numeric IDs also remain visible. New fields require
sensitivity review; this is not automatic PII detection.

Invalid requests omit the body and log only validation field locations and error
types, never rejected values or error messages. Unknown field names are masked.
Bodies without a supported model schema are omitted, including error responses.
Handled HTTP errors can retain the schema-redacted request; unexpected exceptions
omit bodies. Health/docs routes retain their summary-only logging.

Each redacted payload has a 4 KiB UTF-8 JSON limit; larger payloads receive
`{"omitted": "size_limit"}`. Bodies above 64 KiB are not parsed again for logging.
Validation details include at most 20 errors and use the same 4 KiB limit.
These limits affect logs only; API requests and responses are unchanged.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_log_redaction.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_payload_logging.py -q
```

Expected: `9 passed` and `12 passed`, without PostgreSQL. The integration tests
cover redacted requests/responses, nested lists, invalid input, size limits,
missing schemas, and failures. No new dependencies or migrations.

## Project notes

### JavaScript unit tests (F1.1)

Use Node.js 22 or newer with npm (verified with Node 24.20.0). These are
development tools only; the application still runs without Node or a build step.
No npm dependencies are needed for the unit tests because they use Node's built-in
`node:test` and `node:assert/strict` modules with no external dependencies.

From the repository root:

```powershell
npm run test:unit
```

Expected: 3 passed. If PowerShell blocks npm.ps1, use `npm.cmd run test:unit`.
Tests cover empty hashes, known routes, and unknown routes (including inherited
object property names). They import the same `app/ui/routes.js` used by the UI.
`app.js` is loaded with `type="module"` so it can import these functions directly.
No browser, running server or database is required for the unit tests.
These tests do not test Vue rendering; the browser suite below does.

### Browser integration tests (F1.2)

One-time setup from the repository root (requires Node 22+ and the existing
Python `.venv` with application dependencies):

```powershell
npm ci
npx playwright install chromium
npm run test:browser
```

Use `npm.cmd`/`npx.cmd` if PowerShell blocks the corresponding `.ps1` scripts.
Playwright starts a temporary Uvicorn server on port 8766 and stops it after the
run. Keep that port free. No PostgreSQL is needed for these two shell tests.
They cover navigation with Back/Forward and a direct hash URL surviving refresh.
Each test gets a fresh browser context; Chromium runs headlessly, with one worker
and no retries. No screenshots are compared. Video recording is currently enabled
for every test; videos are saved under ignored `test-results/`. Failed runs save a trace under
ignored `test-results/`; inspect it with `npx playwright show-trace <trace.zip>`.
Use `npm run test:browser -- --trace on` to retain traces of passing tests too,
or `npm run test:browser -- --ui` to inspect actions in Playwright UI mode.

To run the same tests against an already-running, rebuilt Compose deployment:

```powershell
$env:UI_BASE_URL = 'http://localhost:8080'
try { npm run test:browser } finally { Remove-Item Env:UI_BASE_URL }
```

This skips temporary-server startup and leaves Compose running. To see the
browser during either run, use `npm run test:browser -- --headed`.
Playwright is a pinned development dependency in package.json/package-lock.json;
neither Node tooling nor test reports are included in the production image.

### UI shell (F1)

Open http://localhost:8080/ui/ with Compose, or http://127.0.0.1:8000/ui/
with local Uvicorn. After changes, rebuild using
`docker --context desktop-linux compose up -d --build --wait`.

FastAPI serves `app/ui/`; the existing Nginx proxy needs no new route. Vue
3.5.13 is stored locally with its MIT license in `app/ui/vendor/` (upstream
`https://unpkg.com/vue@3.5.13/dist/vue.global.prod.js`). There is no Node build
step or runtime CDN request. Python package data includes the UI assets.

Restaurants and Log in are placeholders in this milestone. Click between them,
use Back/Forward, and refresh `/ui/#/login`: the correct heading should appear.
Unknown hashes display Page not found. No restaurant data, cart or login exists
in the UI yet. `/docs` remains available.

Focused verification:
` .\.venv\Scripts\python.exe -m pytest tests/test_ui.py tests/test_health.py tests/test_request_logging.py -q`
(11 passed; two existing dependency warnings). Browser navigation and refresh
were also verified through Nginx. The full database suite was not rerun for F1.

See `AGENTS.md` for the working agreement and `PROGRESS.md` for decisions,
milestones, and review status. Payload logging is accepted; the recorded
performance/metrics scope decisions remain. Database backup implementation was
explicitly skipped; backups remain a production consideration.
