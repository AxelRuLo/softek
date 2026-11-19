
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: UUID
    service_id: UUID


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    service_id: UUID
    service_name: str
    service_description: str
    suggested_price: int
    order_status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
