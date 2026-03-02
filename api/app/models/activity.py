from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActivityType
from app.models.mixins import TimestampMixin, UserTrackMixin


class Activity(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType, name="activitytype"))
    activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attachments: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    opportunity = relationship("Opportunity", back_populates="activities")
    user = relationship("User", back_populates="activities", foreign_keys="Activity.user_id")
