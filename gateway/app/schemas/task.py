from typing import Literal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

TaskStatusValue = Literal["todo", "in_progress", "review", "done", "cancelled"]


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    assigned_to: UUID
    deadline: datetime


class TaskChangeStatus(BaseModel):
    task_id: UUID
    status: TaskStatusValue

class TaskDelete(BaseModel):
    task_id: UUID


class TaskResponse(BaseModel):
    id: UUID
    team_id: UUID
    title: str
    description: str | None
    status: TaskStatusValue
    created_by: UUID
    assigned_to: UUID
    deadline: datetime
    created_at: datetime
    updated_at: datetime
