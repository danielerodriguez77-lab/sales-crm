from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import ApprovalStatus, QuoteStatus


class QuoteBase(BaseModel):
    opportunity_id: int
    number: str | None = None
    status: QuoteStatus = QuoteStatus.draft
    version: int | None = None
    valid_until: date | None = None
    items: list[dict] | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    discount_percent: float | None = None
    approval_status: ApprovalStatus = ApprovalStatus.not_required
    pdf_path: str | None = None
    sent_at: datetime | None = None


class QuoteCreate(QuoteBase):
    pass


class QuoteUpdate(BaseModel):
    status: QuoteStatus | None = None
    valid_until: date | None = None
    items: list[dict] | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    discount_percent: float | None = None
    approval_status: ApprovalStatus | None = None
    pdf_path: str | None = None


class QuoteRead(QuoteBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
