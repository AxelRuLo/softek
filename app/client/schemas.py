import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

NonEmpty = Annotated[str, Field(min_length=1)]


class ClientCreate(BaseModel):
    name: NonEmpty
    email: NonEmpty
    password: NonEmpty

    @field_validator("name", "email", "password")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("invalid email address")
        return value


class ClientUpdate(BaseModel):
    name: NonEmpty | None = None
    email: NonEmpty | None = None
    password: NonEmpty | None = None

    @field_validator("name", "email", "password", mode="before")
    @classmethod
    def validate_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("must not be null")
        return value

    @field_validator("name", "email", "password")
    @classmethod
    def nonblank(cls, value: str) -> str:
        return ClientCreate.nonblank(value)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        return ClientCreate.valid_email(value)


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
