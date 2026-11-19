import os
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.main import app


@pytest.fixture(autouse=True)
def skip_table_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    # Route tests must not modify the configured PostgreSQL database.
    monkeypatch.setattr("app.main.create_db_and_tables", lambda: None)


def test_startup_initializes_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    initialize = Mock()
    monkeypatch.setattr("app.main.create_db_and_tables", initialize)
    with TestClient(app):
        initialize.assert_called_once_with()


def test_startup_fails_if_database_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    initialize = Mock(side_effect=RuntimeError("database unavailable"))
    monkeypatch.setattr("app.main.create_db_and_tables", initialize)
    with pytest.raises(RuntimeError, match="database unavailable"):
        with TestClient(app):
            pass


def test_old_database_health_route_is_removed() -> None:
    with TestClient(app) as client:
        response = client.get("/health/db")

    assert response.status_code == 404


def test_database_health_runs_query(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr("app.main.get_engine", lambda: engine)
    try:
        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "connected"}
    finally:
        engine.dispose()


def test_database_health_missing_url(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_to_get_engine() -> Engine:
        raise RuntimeError("missing URL")

    monkeypatch.setattr("app.main.get_engine", fail_to_get_engine)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_database_health_connection_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = Mock(spec=Engine)
    engine.connect.side_effect = SQLAlchemyError("secret database detail")
    monkeypatch.setattr("app.main.get_engine", lambda: engine)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "secret" not in response.text


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1 to test PostgreSQL"
)
def test_database_health_with_postgres() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
