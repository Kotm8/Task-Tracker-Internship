from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TodoCreate(BaseModel):
    title: str
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None


class TodoResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    completed: bool
    user_id: UUID
    created_at: datetime
    updated_at: datetime
