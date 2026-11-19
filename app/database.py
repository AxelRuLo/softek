import os
from collections.abc import Generator
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session, create_engine


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create one connection pool lazily; no connection is opened here."""
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required; copy .env.example to .env")
    return create_engine(database_url, pool_pre_ping=True)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: provide and close a session for each request."""
    with Session(get_engine()) as session:
        yield session


def create_db_and_tables() -> None:
    """Register all table models and create any missing tables."""
    from app.client import model as client_model
    from app.orders import model as order_model
    from app.service import model as service_model

    tables = [
        client_model.Client.__table__,
        service_model.Service.__table__,
        order_model.Order.__table__,
    ]
    SQLModel.metadata.create_all(get_engine(), tables=tables)
