from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

NonEmptyText = Annotated[str, Field(min_length=1)]
Price = Annotated[int, Field(strict=True, gt=0, le=9223372036854775807)]


class ServiceCreate(BaseModel):
    name: NonEmptyText
    description: NonEmptyText
    suggested_price: Price

    @field_validator("name", "description")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value


class ServiceUpdate(BaseModel):
    name: NonEmptyText | None = None
    description: NonEmptyText | None = None
    suggested_price: Price | None = None

    @field_validator("name", "description", "suggested_price")
    @classmethod
    def nonnull_and_nonblank(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError("Must not be null or blank")
        return value


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    suggested_price: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
