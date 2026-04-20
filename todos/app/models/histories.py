from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.core.enums import TaskActions, TaskStatus
from app.db.database import Base
import uuid
from datetime import datetime, timezone


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    task_id = Column(UUID(as_uuid=True), nullable=False)

    old_status = Column(Enum(TaskStatus, name="task_status_enum"), nullable=True)
    new_status = Column(Enum(TaskStatus, name="task_status_enum"), nullable=False)

    changed_by = Column(UUID(as_uuid=True), nullable=False)

    changed_at = Column(DateTime, default=datetime.now(timezone.utc))


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    task_id = Column(UUID(as_uuid=True), nullable=False)

    action = Column(Enum(TaskActions, name="task_actions_enum"), nullable=False)

    changed_by = Column(UUID(as_uuid=True), nullable=False)

    operation_status = Column(String, nullable=False)  

    changed_at = Column(DateTime, default=datetime.now(timezone.utc))

