import uuid

from sqlalchemy import Column, DateTime, JSON, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consumer_name = Column(String, nullable=False)
    event_id = Column(UUID(as_uuid=True), nullable=False)
    processed_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("consumer_name", "event_id", name="uq_processed_event_consumer_event"),
    )


class AuditEventLog(Base):
    __tablename__ = "audit_event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    event_type = Column(String, nullable=False)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class NotificationEventLog(Base):
    __tablename__ = "notification_event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    event_type = Column(String, nullable=False)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="queued")
    created_at = Column(DateTime, server_default=func.now())
