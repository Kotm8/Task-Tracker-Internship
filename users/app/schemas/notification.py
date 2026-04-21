from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class TaskNotificationRequest(BaseModel):
    user_id: UUID
    task_id: UUID
    team_id: UUID
    event_type: str
    title: str
    description: str | None = None
    deadline: datetime | None = None
    status: str | None = None
    old_status: str | None = None
    new_status: str | None = None


class TaskNotificationResponse(BaseModel):
    status: str
    recipient_email: EmailStr
