from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AlertScope, AlertType
from app.models.mixins import TimestampMixin, UserTrackMixin


class Alert(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(Text)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType, name="alerttype"))
    scope: Mapped[AlertScope] = mapped_column(Enum(AlertScope, name="alertscope"))
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys="Alert.user_id")
    opportunity = relationship("Opportunity")
