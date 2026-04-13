from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enums import TaskStatus
from app.models.tasks import Task
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskChangeStatus, TaskCreate
from app.services.idempotency_service import IdempotencyService

ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.TODO, TaskStatus.REVIEW, TaskStatus.CANCELLED},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.CANCELLED},
    TaskStatus.DONE: {TaskStatus.REVIEW},
    TaskStatus.CANCELLED: {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW},
}

class TaskService:
    def create_task(db: Session, task: TaskCreate, team_id: UUID, created_by: UUID, idempotency_key: UUID):
        idempotency_record = IdempotencyService.validate_request(
            db,
            created_by,
            f"POST:/tasks/{team_id}",
            idempotency_key,
            {
                "team_id": str(team_id),
                "task": task,
            },
        )

        task_repo = TaskRepository(db)
        try:
            db_task = task_repo.create(task, team_id, created_by)
        except Exception:
            idempotency_repo = IdempotencyRepository(db)
            idempotency_repo.delete(idempotency_record)
            raise

        #TODO later save history
        return db_task
    
    def get_user_tasks(db: Session, team_id: UUID, user_id: UUID):
        task_repo = TaskRepository(db)

        return task_repo.get_all_by_user_id_and_team_id(user_id, team_id)

    def get_all_team_tasks(db: Session, team_id: UUID):
        task_repo = TaskRepository(db)
        return task_repo.get_all_by_team_id(team_id)

    def change_task_status(db: Session, team_id: UUID, user_id: UUID, task: TaskChangeStatus, idempotency_key: UUID):
        task_repo = TaskRepository(db)
        idempotency_record = IdempotencyService.validate_request(
            db,
            user_id,
            f"PATCH:/tasks/{team_id}",
            idempotency_key,
            {
                "team_id": str(team_id),
                "task": task,
            },
        )
        
        db_task = task_repo.get_by_task_id_and_user_id_and_team_id(user_id, team_id, task.task_id)
        if not db_task:
            IdempotencyRepository(db).delete(idempotency_record)
            raise HTTPException(status_code=403, detail="Task not found or doesnt belong to user")
        TaskService.validate_status_transition(db_task.status, task.status)

        try:
            return task_repo.update_status(db_task, task.status)
        except Exception:
            IdempotencyRepository(db).delete(idempotency_record)
            raise

    def validate_status_transition(current: TaskStatus, new: TaskStatus):
        if current == new:
            return
    
        if new not in ALLOWED_TRANSITIONS[current]:
            raise HTTPException(status_code=400, detail=f"Invalid transition: {current} -> {new}")
        
    def remove_task(db: Session, user_id: UUID, team_id: UUID, task_id: UUID):
        task_repo = TaskRepository(db)
        db_task = task_repo.get_by_task_id_and_user_id_and_team_id(user_id, team_id, task_id)
        if not db_task:
            raise HTTPException(status_code=403, detail="Task not found or doesnt belong to user")
        task_repo.delete_Task(db_task)
        
