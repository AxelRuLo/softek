
from uuid import UUID

from sqlalchemy import update
from sqlmodel import Session, select

from app.client import Client
from app.orders import Order
from app.service import Service
from app.timestamps import utc_now


def lock_client(session: Session, client_id: UUID) -> Client | None:
    return session.exec(select(Client).where(Client.id == client_id, Client.deleted_at.is_(None)).with_for_update()).first()


def lock_service(session: Session, service_id: UUID) -> Service | None:
    return session.exec(select(Service).where(Service.id == service_id, Service.deleted_at.is_(None)).with_for_update()).first()


def list_orders(session: Session, offset: int, limit: int) -> list[Order]:
    statement = select(Order).where(Order.deleted_at.is_(None)).order_by(Order.created_at, Order.id).offset(offset).limit(limit)
    return list(session.exec(statement).all())


def get_order(session: Session, order_id: UUID) -> Order | None:
    return session.exec(select(Order).where(Order.id == order_id, Order.deleted_at.is_(None)).execution_options(populate_existing=True)).first()


def add_order(session: Session, order: Order) -> Order:
    session.add(order)
    session.flush()
    return order


def cancel_order(session: Session, order_id: UUID) -> Order | None:
    statement = (update(Order).where(Order.id == order_id, Order.deleted_at.is_(None), Order.order_status == "active")
                 .values(order_status="cancel", updated_at=utc_now()).returning(Order))
    order = session.execute(statement.execution_options(populate_existing=True)).scalar_one_or_none()
    return order


def delete_order(session: Session, order_id: UUID) -> bool:
    now = utc_now()
    statement = (update(Order).where(Order.id == order_id, Order.deleted_at.is_(None))
                 .values(deleted_at=now, updated_at=now).returning(Order.id))
    deleted = session.execute(statement).scalar_one_or_none() is not None
    return deleted
