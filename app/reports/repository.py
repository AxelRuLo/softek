from sqlalchemy import func
from sqlmodel import Session, select

from app.client import Client
from app.orders import Order
from app.reports.schemas import ClientSales, RecentSale


def recent_sales(session: Session) -> list[RecentSale]:
    statement = (
        select(Client.name, Order.service_description, Order.suggested_price, Order.created_at)
        .join(Client, Order.client_id == Client.id)
        .where(Order.deleted_at.is_(None), Order.order_status != "cancel")
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(10)
    )
    return [
        RecentSale(
            client_name=name,
            service_description=description,
            suggested_price=price,
            created_at=created_at,
        )
        for name, description, price, created_at in session.exec(statement).all()
    ]


def sales_by_client(session: Session, offset: int, limit: int) -> list[ClientSales]:
    total = func.sum(Order.suggested_price)
    statement = (
        select(Client.id, Client.name, func.count(Order.id), total)
        .join(Order, Order.client_id == Client.id)
        .where(Order.deleted_at.is_(None), Order.order_status != "cancel")
        .group_by(Client.id, Client.name)
        .order_by(total.desc(), Client.id.asc())
        .offset(offset)
        .limit(limit)
    )
    return [
        ClientSales(client_id=client_id, client_name=name, order_count=count, total_cents=amount)
        for client_id, name, count, amount in session.exec(statement).all()
    ]
