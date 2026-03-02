from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OpportunityType, PipelineStage
from app.models.mixins import TimestampMixin, UserTrackMixin


class Opportunity(Base, TimestampMixin, UserTrackMixin):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_type: Mapped[OpportunityType] = mapped_column(
        Enum(OpportunityType, name="opportunitytype")
    )
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    person_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    segment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_value: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    probability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage, name="pipelinestage"), default=PipelineStage.lead_nuevo
    )

    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"), nullable=True)

    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    no_next_action: Mapped[bool] = mapped_column(Boolean, default=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_user = relationship(
        "User", back_populates="assigned_opportunities", foreign_keys="Opportunity.assigned_to_id"
    )
    contact = relationship("Contact", back_populates="opportunities")
    activities = relationship("Activity", back_populates="opportunity")
    quotes = relationship("Quote", back_populates="opportunity")
    sales_orders = relationship("SalesOrder", back_populates="opportunity")
