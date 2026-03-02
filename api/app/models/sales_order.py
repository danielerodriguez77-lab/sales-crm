from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SalesOrderStatus
from app.models.mixins import TimestampMixin, UserTrackMixin


class SalesOrder(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"))
    status: Mapped[SalesOrderStatus] = mapped_column(
        Enum(SalesOrderStatus, name="salesorderstatus"), default=SalesOrderStatus.open
    )
    subtotal: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    tax: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    opportunity = relationship("Opportunity", back_populates="sales_orders")
    quote = relationship("Quote", back_populates="sales_orders")
    invoices = relationship("Invoice", back_populates="sales_order")
