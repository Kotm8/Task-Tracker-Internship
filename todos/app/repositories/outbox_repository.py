from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.task_events import OutboxStatus, TaskEventEnvelope
from app.models.outbox import OutboxEvent


class OutboxRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, event: TaskEventEnvelope) -> OutboxEvent:
        db_event = OutboxEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            routing_key=event.event_type,
            producer=event.producer,
            correlation_id=event.correlation_id,
            version=event.version,
            payload=event.payload,
            status=OutboxStatus.PENDING.value,
            occurred_at=event.occurred_at,
        )
        self.db.add(db_event)
        self.db.flush()
        self.db.refresh(db_event)
        return db_event

    def lock_batch(self, limit: int) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status.in_([OutboxStatus.PENDING.value, OutboxStatus.FAILED.value]))
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(self.db.scalars(stmt).all())

    def mark_published(self, db_event: OutboxEvent) -> None:
        db_event.status = OutboxStatus.PUBLISHED.value
        db_event.attempts += 1
        db_event.last_error = None
        db_event.published_at = datetime.now(timezone.utc)
        self.db.flush()

    def mark_failed(self, db_event: OutboxEvent, error_message: str) -> None:
        db_event.status = OutboxStatus.FAILED.value
        db_event.attempts += 1
        db_event.last_error = error_message
        self.db.flush()
