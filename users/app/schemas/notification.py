from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


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


EVENT_VERSION = 1
EVENT_PRODUCER = "todo_api"

class TaskEventEnvelope(BaseModel):
    event_id: UUID
    event_type: str
    occurred_at: datetime
    producer: str = EVENT_PRODUCER
    correlation_id: UUID | None = None
    version: int = EVENT_VERSION
    payload: dict[str, Any]
