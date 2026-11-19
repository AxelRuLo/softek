from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import create_db_and_tables, get_engine
from app.client.router import router as client_router
from app.orders.router import router as orders_router
from app.service.router import router as service_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="REST API SOFTEK", lifespan=lifespan)
app.include_router(client_router)
app.include_router(service_router)
app.include_router(orders_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Check that the configured database can accept and run a query."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ok", "database": "connected"}
