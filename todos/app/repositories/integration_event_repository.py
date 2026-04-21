from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.task_events import TaskEventEnvelope
from app.models.integration_events import AuditEventLog, NotificationEventLog, ProcessedEvent


class IntegrationEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def is_processed(self, consumer_name: str, event_id) -> bool:
        stmt = (
            select(ProcessedEvent)
            .where(ProcessedEvent.consumer_name == consumer_name)
            .where(ProcessedEvent.event_id == event_id)
        )
        return self.db.scalar(stmt) is not None

    def mark_processed(self, consumer_name: str, event_id) -> ProcessedEvent:
        processed = ProcessedEvent(
            consumer_name=consumer_name,
            event_id=event_id,
        )
        self.db.add(processed)
        self.db.flush()
        self.db.refresh(processed)
        return processed

    def create_audit_log(self, event: TaskEventEnvelope) -> AuditEventLog:
        log_entry = AuditEventLog(
            event_id=event.event_id,
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            payload=event.payload,
        )
        self.db.add(log_entry)
        self.db.flush()
        self.db.refresh(log_entry)
        return log_entry

    def create_notification_log(self, event: TaskEventEnvelope) -> NotificationEventLog:
        log_entry = NotificationEventLog(
            event_id=event.event_id,
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            payload=event.payload,
            status="queued",
        )
        self.db.add(log_entry)
        self.db.flush()
        self.db.refresh(log_entry)
        return log_entry

    def get_notification_log_by_event_id(self, event_id: UUID) -> NotificationEventLog | None:
        stmt = select(NotificationEventLog).where(NotificationEventLog.event_id == event_id)
        return self.db.scalar(stmt)

    def update_notification_log_status(
        self,
        log_entry: NotificationEventLog,
        status: str,
    ) -> NotificationEventLog:
        log_entry.status = status
        self.db.flush()
        self.db.refresh(log_entry)
        return log_entry

    def get_audit_log(self, team_id: UUID) -> list[AuditEventLog]:
        stmt = (
            select(AuditEventLog)
            .where(AuditEventLog.payload["team_id"].as_string() == str(team_id))
            .order_by(AuditEventLog.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())
