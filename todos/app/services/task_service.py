from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.enums import TaskActions, TaskStatus
from app.core.task_events import (
    build_task_created_event,
    build_task_deleted_event,
    build_task_status_changed_event,
)
from app.repositories.task_repository import TaskRepository
from app.repositories.outbox_repository import OutboxRepository
from app.schemas.task import TaskChangeStatus, TaskCreate
from app.services.idempotency_service import IdempotencyService
from app.repositories.history_repository import HistoryRepository

ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.TODO, TaskStatus.REVIEW, TaskStatus.CANCELLED},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.CANCELLED},
    TaskStatus.DONE: {TaskStatus.REVIEW},
    TaskStatus.CANCELLED: {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW},
}

class TaskService:
    def create_task(db: Session, task: TaskCreate, team_id: UUID, created_by: UUID, idempotency_key: UUID):
        task_repo = TaskRepository(db)
        history_repo = HistoryRepository(db)
        outbox_repo = OutboxRepository(db)
        try:
            IdempotencyService.validate_request(
                db,
                created_by,
                f"POST:/tasks/{team_id}",
                idempotency_key,
                {
                    "team_id": str(team_id),
                    "task": task,
                },
            )

            db_task = task_repo.create(task, team_id, created_by)
            history_repo.save_task_action(db_task.id, TaskActions.CREATE, created_by, True, datetime.now(timezone.utc))
            outbox_repo.create(build_task_created_event(db_task, correlation_id=idempotency_key))
            db.commit()
            db.refresh(db_task)
            return db_task
        except Exception:
            db.rollback()
            raise
    
    def get_user_tasks(
        db: Session,
        user_id: UUID,
        team_id: UUID, 
        status=None,
        deadline=None,
        sort=None,
        direction="asc",
        limit=10,
        page=1,
    ):
        task_repo = TaskRepository(db)

        return task_repo.get_user_tasks(
            user_id=user_id,
            team_id=team_id, 
            status=status,
            deadline=deadline,
            sort=sort,
            direction=direction,
            limit=limit,
            page=page
            )

    def get_all_team_tasks(
        db: Session,
        team_id: UUID | None = None,
        status=None,
        deadline=None,
        sort=None,
        direction="asc",
        limit=10,
        page=1,
    ):
        task_repo = TaskRepository(db)
        return task_repo.get_user_tasks(
            team_id=team_id, 
            status=status,
            deadline=deadline,
            sort=sort,
            direction=direction,
            limit=limit,
            page=page
            )

    def change_task_status(db: Session, team_id: UUID, user_id: UUID, task: TaskChangeStatus, idempotency_key: UUID):
        task_repo = TaskRepository(db)
        history_repo = HistoryRepository(db)
        outbox_repo = OutboxRepository(db)
        
        db_task = task_repo.get_by_task_id_and_user_id_and_team_id(user_id, team_id, task.task_id)
        if not db_task:
            raise HTTPException(status_code=403, detail="Task not found or doesnt belong to user")
        TaskService.validate_status_transition(db_task.status, task.status)
        old_status = db_task.status

        try:
            IdempotencyService.validate_request(
                db,
                user_id,
                f"PATCH:/tasks/{team_id}",
                idempotency_key,
                {
                    "team_id": str(team_id),
                    "task": task,
                },
            )

            history_repo.save_task_action(db_task.id, TaskActions.CHANGED, user_id, True, datetime.now(timezone.utc))
            history_repo.save_status_change(task.task_id, old_status, task.status, user_id, datetime.now(timezone.utc))
            updated_task = task_repo.update_status(db_task, task.status)
            outbox_repo.create(
                build_task_status_changed_event(
                    updated_task,
                    old_status=old_status,
                    new_status=task.status,
                    changed_by=user_id,
                    correlation_id=idempotency_key,
                )
            )
            db.commit()
            db.refresh(updated_task)
            return updated_task
        except Exception:
            db.rollback()
            raise

    def validate_status_transition(current: TaskStatus, new: TaskStatus):
        if current == new:
            return
    
        if new not in ALLOWED_TRANSITIONS[current]:
            raise HTTPException(status_code=400, detail=f"Invalid transition: {current} -> {new}")
        
    def remove_task(db: Session, user_id: UUID, team_id: UUID, task_id: UUID):
        history_repo = HistoryRepository(db)
        task_repo = TaskRepository(db)
        outbox_repo = OutboxRepository(db)
        db_task = task_repo.get_by_task_id_and_team_id(team_id, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found in this team")
        response_payload = {
            "id": db_task.id,
            "team_id": db_task.team_id,
            "title": db_task.title,
            "description": db_task.description,
            "status": db_task.status,
            "created_by": db_task.created_by,
            "assigned_to": db_task.assigned_to,
            "deadline": db_task.deadline,
            "created_at": db_task.created_at,
            "updated_at": db_task.updated_at,
        }

        try:
            history_repo.save_task_action(
                db_task.id,
                TaskActions.DELETED,
                user_id,
                True,
                datetime.now(timezone.utc),
            )
            outbox_repo.create(build_task_deleted_event(db_task, deleted_by=user_id))
            task_repo.delete_Task(db_task)
            db.commit()
            return response_payload
        except Exception:
            db.rollback()
            raise
        
