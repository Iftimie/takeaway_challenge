# Takeaway Service

A take-home backend built one small milestone at a time. Exposes customer
registration at `POST /auth/register` and `GET /health`, returning HTTP 200 with
`{"status":"ok"}`. Health checks application liveness, not database readiness.

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
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
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
docker compose config --quiet
docker compose up -d --wait db
docker compose ps
```

Expected: `db` reports healthy. The first startup downloads the PostgreSQL image.
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

Expected: `29 passed, 1 deselected`. Tests check connectivity, user-table
constraints, and registration. Tests insert rows inside transactions and roll them back after
each test. The default `pytest -q` command runs all tests, including integration
tests. VS Code can also discover and run individual tests without a marker override:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: `30 passed` when PostgreSQL is running and migrations are applied.
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

Expected: revision `0002 (head)` after upgrading. `upgrade head` applies pending
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
- Passwords are 15-128 characters and are never trimmed. No special-character
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

Email format validation does not verify mailbox ownership. Verification emails,
login, and JWT issuance are not part of this milestone. Login must use the same
email normalization policy when implemented.

## Project notes

See `AGENTS.md` for the working agreement and `PROGRESS.md` for decisions,
milestones, and review status. Login, JWT authentication, and full deployment
belong to later milestones.
