import os

import pytest
from sqlalchemy import create_engine, inspect, text

from app.database import create_db_and_tables, get_engine


def test_engine_uses_postgres_without_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://app:app@localhost:1/app"
    )
    get_engine.cache_clear()
    engine = get_engine()
    try:
        assert engine.url.drivername == "postgresql+psycopg"
    finally:
        engine.dispose()
        get_engine.cache_clear()


def test_create_db_and_tables_is_repeatable(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr("app.database.get_engine", lambda: engine)
    try:
        create_db_and_tables()
        create_db_and_tables()
        assert {"clients", "services", "orders"}.issubset(
            inspect(engine).get_table_names()
        )
    finally:
        engine.dispose()


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1 to test PostgreSQL"
)
def test_postgres_connection() -> None:
    with get_engine().connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
