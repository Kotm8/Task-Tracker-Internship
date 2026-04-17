import uuid

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.task_events import OutboxStatus
from app.db.database import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    event_type = Column(String, nullable=False)
    routing_key = Column(String, nullable=False)
    producer = Column(String, nullable=False)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default=OutboxStatus.PENDING.value)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    occurred_at = Column(DateTime, nullable=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
