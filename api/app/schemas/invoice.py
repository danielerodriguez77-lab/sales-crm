from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import InvoiceStatus, InvoiceType


class InvoiceBase(BaseModel):
    sales_order_id: int
    number: str | None = None
    issue_date: date
    due_date: date
    total: float
    status: InvoiceStatus = InvoiceStatus.draft
    invoice_type: InvoiceType = InvoiceType.total


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    sales_order_id: int | None = None
    number: str | None = None
    issue_date: date | None = None
    due_date: date | None = None
    total: float | None = None
    status: InvoiceStatus | None = None
    invoice_type: InvoiceType | None = None


class InvoiceRead(InvoiceBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
