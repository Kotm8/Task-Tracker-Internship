from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.models.tasks import Task
from app.core.enums import TaskStatus


EVENT_VERSION = 1
EVENT_PRODUCER = "todo_api"


class TaskEventType(StrEnum):
    TASK_CREATED = "task.created"
    TASK_STATUS_CHANGED = "task.status_changed"
    TASK_DELETED = "task.deleted"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class TaskEventEnvelope(BaseModel):
    event_id: UUID
    event_type: str
    occurred_at: datetime
    producer: str = EVENT_PRODUCER
    correlation_id: UUID | None = None
    version: int = EVENT_VERSION
    payload: dict[str, Any]


def _base_task_payload(task: Task) -> dict[str, Any]:
    return jsonable_encoder(
        {
            "task_id": task.id,
            "team_id": task.team_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "created_by": task.created_by,
            "assigned_to": task.assigned_to,
            "deadline": task.deadline,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
    )


def build_task_created_event(task: Task, correlation_id: UUID | None = None) -> TaskEventEnvelope:
    return TaskEventEnvelope(
        event_id=uuid4(),
        event_type=TaskEventType.TASK_CREATED,
        occurred_at=datetime.now(timezone.utc),
        correlation_id=correlation_id,
        payload=_base_task_payload(task),
    )


def build_task_status_changed_event(
    task: Task,
    old_status: str,
    new_status: str,
    changed_by: UUID,
    correlation_id: UUID | None = None,
) -> TaskEventEnvelope:
    payload = _base_task_payload(task)
    payload.update(
        {
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by,
        }
    )
    payload = jsonable_encoder(payload)
    return TaskEventEnvelope(
        event_id=uuid4(),
        event_type=TaskEventType.TASK_STATUS_CHANGED,
        occurred_at=datetime.now(timezone.utc),
        correlation_id=correlation_id,
        payload=payload,
    )


def build_task_deleted_event(task: Task, deleted_by: UUID, correlation_id: UUID | None = None) -> TaskEventEnvelope:
    payload = _base_task_payload(task)
    payload["deleted_by"] = deleted_by
    payload = jsonable_encoder(payload)
    return TaskEventEnvelope(
        event_id=uuid4(),
        event_type=TaskEventType.TASK_DELETED,
        occurred_at=datetime.now(timezone.utc),
        correlation_id=correlation_id,
        payload=payload,
    )
