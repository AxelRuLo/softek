"""Order table with independent service snapshot fields."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint
from sqlmodel import Field, SQLModel

from app.timestamps import utc_now


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "length(trim(service_name)) > 0", name="ck_orders_service_name_nonempty"
        ),
        CheckConstraint(
            "length(trim(service_description)) > 0",
            name="ck_orders_service_description_nonempty",
        ),
        CheckConstraint("suggested_price > 0", name="ck_orders_positive_price"),
        CheckConstraint(
            "order_status IN ('active', 'cancel')", name="ck_orders_valid_status"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(foreign_key="clients.id")
    service_id: UUID = Field(foreign_key="services.id")

    # These values are copied when an order is created, not read from Service later.
    service_name: Annotated[str, Field(min_length=1)]
    service_description: Annotated[str, Field(min_length=1)]
    suggested_price: Annotated[int, Field(gt=0, sa_type=BigInteger)]
    order_status: str = Field(default="active")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now}
    )
    deleted_at: datetime | None = Field(default=None)
