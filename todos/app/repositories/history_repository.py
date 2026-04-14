from sqlalchemy import DateTime
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.enums import TaskActions, TaskStatus
from app.models.histories import TaskHistory, TaskStatusHistory


class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_task_action(self, task_id: UUID, action: TaskActions, changed_by: UUID, operation_status: bool, changed_at: DateTime):
        db_task_action = TaskHistory(
            task_id=task_id,
            action=action,
            changed_by=changed_by,
            operation_status=operation_status,
            changed_at=changed_at
        )
        self.db.add(db_task_action)
        self.db.commit()
        self.db.refresh(db_task_action)
        return db_task_action
    
    def save_status_change(self, task_id: UUID, old_status: TaskStatus, new_status: TaskStatus, changed_by: UUID, changed_at: DateTime):
        db_task_status = TaskStatusHistory(
            task_id=task_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            changed_at=changed_at
        )
        self.db.add(db_task_status)
        self.db.commit()
        self.db.refresh(db_task_status)
        return db_task_status

    def delete_task_action(self, action_history: TaskHistory):
        self.db.delete(action_history)
        self.db.commit()
    
        
    def delete_task_status_change(self, status_history: TaskStatusHistory):
        self.db.delete(status_history)
        self.db.commit()