from datetime import datetime

from pydantic import BaseModel

from app.models.enums import SalesOrderStatus


class SalesOrderBase(BaseModel):
    opportunity_id: int
    quote_id: int
    status: SalesOrderStatus = SalesOrderStatus.open
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    reference: str | None = None
    order_date: datetime | None = None


class SalesOrderCreate(SalesOrderBase):
    pass


class SalesOrderUpdate(BaseModel):
    status: SalesOrderStatus | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    reference: str | None = None


class SalesOrderRead(SalesOrderBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SalesOrderFromOpportunity(BaseModel):
    opportunity_id: int
    quote_id: int | None = None
