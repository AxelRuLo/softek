
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, update
from sqlmodel import Session, select

from app.client import Client


def get(session: Session, client_id: UUID) -> Client | None:
    return session.exec(
        select(Client).where(Client.id == client_id, Client.deleted_at.is_(None))
    ).first()


def list_active(session: Session, offset: int, limit: int) -> list[Client]:
    query = (
        select(Client)
        .where(Client.deleted_at.is_(None))
        .order_by(Client.created_at, Client.id)
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(query).all())


def email_exists(session: Session, email: str, exclude_id: UUID | None = None) -> bool:
    query = select(Client.id).where(
        Client.deleted_at.is_(None), func.lower(Client.email) == func.lower(email)
    )
    if exclude_id is not None:
        query = query.where(Client.id != exclude_id)
    return session.exec(query).first() is not None


def add(session: Session, client: Client) -> None:
    session.add(client)
    session.flush()


def update_active(session: Session, client_id: UUID, values: dict) -> Client | None:
    result = session.execute(
        update(Client)
        .where(Client.id == client_id, Client.deleted_at.is_(None))
        .values(**values)
    )
    if result.rowcount == 0:
        return None
    return get(session, client_id)


def soft_delete(session: Session, client_id: UUID, deleted_at: datetime) -> bool:
    result = session.execute(
        update(Client)
        .where(Client.id == client_id, Client.deleted_at.is_(None))
        .values(deleted_at=deleted_at)
    )
    return result.rowcount > 0
