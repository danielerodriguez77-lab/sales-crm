from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApprovalStatus, QuoteStatus
from app.models.mixins import TimestampMixin, UserTrackMixin


class Quote(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[QuoteStatus] = mapped_column(
        Enum(QuoteStatus, name="quotestatus"), default=QuoteStatus.draft
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    items: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    subtotal: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    tax: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approvalstatus"), default=ApprovalStatus.not_required
    )
    pdf_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    opportunity = relationship("Opportunity", back_populates="quotes")
    sales_orders = relationship("SalesOrder", back_populates="quote")
    created_by = relationship("User", foreign_keys="Quote.created_by_id", back_populates="quotes")
