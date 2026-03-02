from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AlertScope, AlertType


class AlertRead(BaseModel):
    id: int
    message: str
    alert_type: AlertType
    scope: AlertScope
    opportunity_id: int | None = None
    user_id: int | None = None
    resolved_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True
