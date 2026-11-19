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

Visit <http://127.0.0.1:8000/docs> for the interactive API docs. `GET /health` opens a connection, runs `SELECT 1`, and returns `{"status":"ok","database":"connected"}` or HTTP 503 with a generic error if the database is unavailable. It checks **database readiness**, not just whether the API process is running. Don't use it as a liveness probe that restarts the API when PostgreSQL is unavailable. SQLModel `table=True` entities live in `app/client/model.py`, `app/service/model.py`, and `app/orders/model.py`. At startup, the API imports all three models and uses `SQLModel.metadata.create_all()` to create missing tables. PostgreSQL must be available before the API starts. **`create_all()` does not update existing tables or migrate data** when models change. No domain API routes have been added yet; order creation and snapshot immutability rules must be enforced in a later step. Don't return the Client table model directly from API routes: use a public response model without its password hash.

Each entity has UTC `created_at` and `updated_at` values managed by SQLModel/SQLAlchemy. ORM updates (including future cancellation and soft deletion) refresh `updated_at`; SQL executed outside the ORM does not. `deleted_at` stays empty until soft deletion.

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

Stop the local database with `docker compose down` (add `-v` **only** if you want to delete its data).
