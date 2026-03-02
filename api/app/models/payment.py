from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PaymentMethod
from app.models.mixins import TimestampMixin, UserTrackMixin


class Payment(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    date: Mapped[date] = mapped_column(Date)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="paymentmethod"))
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
