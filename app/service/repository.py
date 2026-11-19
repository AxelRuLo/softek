from datetime import datetime
from uuid import UUID

from sqlalchemy import update
from sqlmodel import Session, select

from app.service import Service


def get_active(session: Session, service_id: UUID) -> Service | None:
    return session.exec(select(Service).where(Service.id == service_id, Service.deleted_at.is_(None))).first()


def list_active(session: Session, offset: int, limit: int) -> list[Service]:
    statement = (select(Service).where(Service.deleted_at.is_(None))
                 .order_by(Service.created_at, Service.id).offset(offset).limit(limit))
    return list(session.exec(statement).all())


def save(session: Session, item: Service) -> Service:
    session.add(item)
    session.flush()
    return item


def update_active(session: Session, service_id: UUID, values: dict) -> Service | None:
    changes = values if values else {"updated_at": Service.updated_at}
    statement = (update(Service).where(Service.id == service_id, Service.deleted_at.is_(None))
                 .values(**changes).returning(Service))
    return session.execute(statement.execution_options(populate_existing=True)).scalar_one_or_none()


def delete_active(session: Session, service_id: UUID, deleted_at: datetime) -> bool:
    statement = (update(Service).where(Service.id == service_id, Service.deleted_at.is_(None))
                 .values(deleted_at=deleted_at).returning(Service.id))
    return session.execute(statement).scalar_one_or_none() is not None
