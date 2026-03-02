from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ActivityType


class ActivityBase(BaseModel):
    opportunity_id: int
    activity_type: ActivityType
    activity_at: datetime
    outcome: str | None = None
    notes: str | None = None
    next_action_at: datetime | None = None
    attachments: dict | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    activity_type: ActivityType | None = None
    activity_at: datetime | None = None
    outcome: str | None = None
    notes: str | None = None
    next_action_at: datetime | None = None
    attachments: dict | None = None


class ActivityRead(ActivityBase):
    id: int
    user_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
