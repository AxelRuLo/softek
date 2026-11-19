"""Client table and active-email uniqueness rule."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, func
from sqlmodel import Field, SQLModel

from app.timestamps import utc_now


class Client(SQLModel, table=True):
    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_clients_name_nonempty"),
        CheckConstraint("length(trim(email)) > 0", name="ck_clients_email_nonempty"),
        CheckConstraint(
            "length(trim(password_hash)) > 0", name="ck_clients_password_hash_nonempty"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: Annotated[str, Field(min_length=1)]
    email: Annotated[str, Field(min_length=1)]
    password_hash: Annotated[str, Field(min_length=1, exclude=True, repr=False)]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now}
    )
    deleted_at: datetime | None = Field(default=None)


Index(
    "uq_clients_active_email_lower",
    func.lower(Client.email),
    unique=True,
    postgresql_where=Client.deleted_at.is_(None),
    sqlite_where=Client.deleted_at.is_(None),
)
