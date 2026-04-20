from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from app.core.enums import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    assigned_to: UUID
    deadline: datetime


class TaskChangeStatus(BaseModel):
    task_id: UUID
    status: TaskStatus

class TaskDelete(BaseModel):
    task_id: UUID


class TaskResponse(BaseModel):
    id: UUID
    team_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    created_by: UUID
    assigned_to: UUID
    deadline: datetime
    created_at: datetime
    updated_at: datetime


class PaginatedTaskResponse(BaseModel):
    items: list[TaskResponse]
    page: int
    limit: int
    total: int
