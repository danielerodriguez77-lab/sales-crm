from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InvoiceStatus, InvoiceType
from app.models.mixins import TimestampMixin, UserTrackMixin


class Invoice(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"))
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    total: Mapped[float] = mapped_column(Numeric(12, 2))
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoicestatus"), default=InvoiceStatus.draft
    )
    invoice_type: Mapped[InvoiceType] = mapped_column(
        Enum(InvoiceType, name="invoicetype"), default=InvoiceType.total
    )

    sales_order = relationship("SalesOrder", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")
