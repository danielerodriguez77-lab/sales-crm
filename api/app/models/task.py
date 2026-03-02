from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TaskStatus, TaskType
from app.models.mixins import TimestampMixin, UserTrackMixin


class Task(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="taskstatus"), default=TaskStatus.open
    )
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType, name="tasktype"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True)

    user = relationship("User", foreign_keys="Task.user_id")
    opportunity = relationship("Opportunity")
