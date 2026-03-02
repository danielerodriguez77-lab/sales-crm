from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TaskStatus, TaskType


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    due_at: datetime | None = None
    status: TaskStatus = TaskStatus.open
    task_type: TaskType
    user_id: int
    opportunity_id: int | None = None


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    due_at: datetime | None = None
    description: str | None = None


class TaskRead(TaskBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
