# REST API starter

Python 3.12 + FastAPI + PostgreSQL + SQLModel (Pydantic + SQLAlchemy) + pytest.

## Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
docker compose up -d db
```

The container listens on host port **5433** (and port 5432 inside the container), so it won't collide with a PostgreSQL server already using host port 5432. The database credentials in `compose.yaml` and `.env.example` are for **local development only**. Replace them and manage secrets securely for deployment. The database URL uses the `psycopg` (v3) SQLAlchemy driver. If you already have PostgreSQL, skip Compose and set `DATABASE_URL` in `.env` to your own connection string. Docker access is required for Compose; if your user cannot access `/var/run/docker.sock`, configure Docker permissions through your system administrator or use an existing PostgreSQL instance instead.

## Run the API

```bash
python -m uvicorn app.main:app --reload
```

Visit <http://127.0.0.1:8000/docs> for the interactive API docs. `GET /health` opens a connection, runs `SELECT 1`, and returns `{"status":"ok","database":"connected"}` or HTTP 503 with a generic error if the database is unavailable. It checks **database readiness**, not just whether the API process is running. Don't use it as a liveness probe that restarts the API when PostgreSQL is unavailable. SQLModel entities live in `app/client/model.py`, `app/service/model.py`, and `app/orders/model.py` and are exported by their packages. At startup, the API creates missing entity tables using `SQLModel.metadata.create_all()`. PostgreSQL must be available before the API starts. **`create_all()` does not update existing tables or migrate data** when models change.

Each entity has UTC `created_at` and `updated_at` values managed by SQLModel/SQLAlchemy. ORM updates (including future cancellation and soft deletion) refresh `updated_at`; SQL executed outside the ORM does not. `deleted_at` stays empty until soft deletion.

## CRUD endpoints

**Authentication is not implemented yet. All CRUD routes are currently public; do not expose this service to an untrusted network.** Client passwords are hashed with Argon2 and are not returned in responses.

Use `GET` and `POST` on `/services` and `/clients`, and `GET`, `PUT`, `PATCH`, and `DELETE` on their `/{id}` routes. `/orders` supports `GET`, `POST`, `GET /{id}`, `DELETE /{id}`, and `POST /{id}/cancel`; order snapshots cannot be edited through the API. Lists support `offset` and `limit` (default 20, maximum 100). DELETE performs a soft delete and returns 204.

### Sales reports

- `GET /reports/sales/recent`: up to ten most recent non-cancelled, non-deleted orders. Includes the client's current name and the service description and price captured on the order.
- `GET /reports/sales/by-client`: order count and total cents per client, ordered by total descending. Supports `offset` and `limit` (default 20, maximum 100).

Both reports retain sales belonging to soft-deleted clients. Amounts are integers in cents.

### Postman collection

Import `postman_collection.json` into Postman and set the `base_url` collection variable if needed. Create a client and a service before creating an order; successful creation responses save their IDs as collection variables. A failed request leaves the previous ID unchanged, so check the selected IDs before updating, cancelling, or deleting. These manual requests modify the configured database; use a disposable development database and sample credentials.

Check the database endpoint while the API is running:

```bash
curl -i http://127.0.0.1:8000/health
```

## Tests

```bash
python -m pytest
```

The normal test run does not require a running database. To also check a real PostgreSQL connection, first start PostgreSQL and configure `.env`, then run:

```bash
RUN_DB_TESTS=1 python -m pytest
```

The functional sales workflow can be run separately with `python -m pytest -q tests/test_functional.py`. It exercises valid and invalid creation requests and both reports using an isolated in-memory SQLite database; it does not write to PostgreSQL. The optional PostgreSQL checks above verify connectivity, not the complete functional workflow on PostgreSQL.

### Test map

```text
tests/
|
|-- test_database.py
|   |-- PostgreSQL engine configuration without connecting
|   |-- Repeatable table creation                       [SQLite]
|   `-- PostgreSQL connection with SELECT 1             [PostgreSQL*]
|
|-- test_main.py
|   |-- Startup initialization and failure               [mock]
|   |-- Removed /health/db route returns 404
|   |-- /health succeeds                                 [SQLite]
|   |-- /health failures return 503                       [mock]
|   `-- /health succeeds against PostgreSQL              [PostgreSQL*]
|
|-- test_models.py                                      [SQLite]
|   |-- UUIDs, initial order status and UTC timestamps
|   |-- Validation, password-hash exclusion and constraints
|   |-- Active uniqueness and reuse after soft deletion
|   `-- Order snapshot remains unchanged
|
`-- test_functional.py                                  [SQLite]
    `-- Sales workflow
        |-- Valid, invalid and duplicate client creation
        |-- Valid, invalid and duplicate service creation
        |-- Valid and invalid order creation
        |-- Snapshot, cancellation and soft deletion
        `-- Sales reports, filters, ordering and pagination
```

`[PostgreSQL*]` tests run only with `RUN_DB_TESTS=1`. This flag does **not** switch the SQLite tests to PostgreSQL.

Stop the local database with `docker compose down` (add `-v` **only** if you want to delete its data).
