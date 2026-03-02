from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin, UserTrackMixin


class User(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="userrole"), default=UserRole.seller)
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    team: Mapped[str | None] = mapped_column(String(100), nullable=True)

    assigned_opportunities = relationship(
        "Opportunity", back_populates="assigned_user", foreign_keys="Opportunity.assigned_to_id"
    )
    activities = relationship("Activity", back_populates="user", foreign_keys="Activity.user_id")
    quotes = relationship("Quote", back_populates="created_by", foreign_keys="Quote.created_by_id")
