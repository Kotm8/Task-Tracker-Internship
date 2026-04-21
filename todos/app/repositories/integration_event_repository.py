from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.task_events import TaskEventEnvelope
from app.models.integration_events import (
    AuditEventLog,
    NotificationEventLog,
    ProcessedEvent,
    ProcessingErrorLog,
)


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

    def create_processing_error_log(
        self,
        *,
        consumer_name: str,
        event_id: UUID | None,
        event_type: str | None,
        team_id: UUID | None,
        payload: dict | None,
        error_type: str,
        error_text: str,
    ) -> ProcessingErrorLog:
        error_log = ProcessingErrorLog(
            consumer_name=consumer_name,
            event_id=event_id,
            event_type=event_type,
            team_id=team_id,
            payload=payload,
            error_type=error_type,
            error_text=error_text,
        )
        self.db.add(error_log)
        self.db.flush()
        self.db.refresh(error_log)
        return error_log

    def get_audit_log(self, team_id: UUID) -> list[AuditEventLog]:
        stmt = (
            select(AuditEventLog)
            .where(AuditEventLog.payload["team_id"].as_string() == str(team_id))
            .order_by(AuditEventLog.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_processing_error_logs(self, team_id: UUID) -> list[ProcessingErrorLog]:
        stmt = (
            select(ProcessingErrorLog)
            .where(ProcessingErrorLog.team_id == team_id)
            .order_by(ProcessingErrorLog.failed_at.asc())
        )
        return list(self.db.scalars(stmt).all())
