from __future__ import annotations

from datetime import date as dt_date, datetime

from pydantic import BaseModel

from app.models.enums import PaymentMethod


class PaymentBase(BaseModel):
    invoice_id: int
    amount: float
    date: dt_date
    method: PaymentMethod
    reference: str | None = None
    attachment_path: str | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount: float | None = None
    date: dt_date | None = None
    method: PaymentMethod | None = None
    reference: str | None = None
    attachment_path: str | None = None


class PaymentRead(PaymentBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
