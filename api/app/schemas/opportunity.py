from datetime import datetime

from pydantic import BaseModel

from app.models.enums import OpportunityType, PipelineStage


class OpportunityBase(BaseModel):
    record_type: OpportunityType
    company_name: str | None = None
    person_name: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    segment: str | None = None
    estimated_value: float | None = None
    probability: int | None = None
    stage: PipelineStage = PipelineStage.lead_nuevo
    assigned_to_id: int | None = None
    contact_id: int | None = None
    next_action_at: datetime | None = None
    no_next_action: bool = False
    notes: str | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    company_name: str | None = None
    person_name: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    segment: str | None = None
    estimated_value: float | None = None
    probability: int | None = None
    stage: PipelineStage | None = None
    assigned_to_id: int | None = None
    contact_id: int | None = None
    next_action_at: datetime | None = None
    no_next_action: bool | None = None
    notes: str | None = None
    allow_unpaid_close: bool | None = None


class OpportunityRead(OpportunityBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
