# REST API starter

Python 3.12 + FastAPI + PostgreSQL + SQLAlchemy 2.x + pytest.

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

Visit <http://127.0.0.1:8000/docs> for the interactive API docs or <http://127.0.0.1:8000/health> for a liveness check. `/health` intentionally does **not** check PostgreSQL. Import `Base` for future ORM models and `get_session` from `app.database` as a FastAPI dependency in future database-backed routes; sessions are closed after each request. Database connections are created only when first needed. No tables or migrations are created yet; add those when the data model is defined.

## Tests

```bash
python -m pytest
```

The normal test run does not require a running database. To also check a real PostgreSQL connection, first start PostgreSQL and configure `.env`, then run:

```bash
RUN_DB_TESTS=1 python -m pytest
```

Stop the local database with `docker compose down` (add `-v` **only** if you want to delete its data).

## Git and GitHub

This directory is initialized as a **local Git repository**. A GitHub repository and remote must be created separately with your GitHub account before pushing; don't commit `.env` or `.venv/`.
