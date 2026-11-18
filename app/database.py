import os
from collections.abc import Generator
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    """Base class for future SQLAlchemy ORM models."""


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
