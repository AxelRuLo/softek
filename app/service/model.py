"""Service table and active-name uniqueness rule."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, Index
from sqlmodel import Field, SQLModel

from app.timestamps import utc_now


class Service(SQLModel, table=True):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_services_name_nonempty"),
        CheckConstraint(
            "length(trim(description)) > 0", name="ck_services_description_nonempty"
        ),
        CheckConstraint("suggested_price > 0", name="ck_services_positive_price"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    suggested_price: Annotated[int, Field(gt=0, sa_type=BigInteger)]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now}
    )
    deleted_at: datetime | None = Field(default=None)


Index(
    "uq_services_active_name",
    Service.name,
    unique=True,
    postgresql_where=Service.deleted_at.is_(None),
    sqlite_where=Service.deleted_at.is_(None),
)
