from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecentSale(BaseModel):
    client_name: str
    service_description: str
    suggested_price: int
    created_at: datetime


class ClientSales(BaseModel):
    client_id: UUID
    client_name: str
    order_count: int
    total_cents: int
