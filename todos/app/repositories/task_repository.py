from uuid import UUID
from sqlalchemy.orm import Session
from app.schemas.task import TaskCreate
from app.core.enums import TaskStatus
from app.models.tasks import Task


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_user_id_and_team_id(self, user_id: UUID, team_id: UUID):
        return (
            self.db.query(Task)
            .filter(Task.assigned_to == user_id)
            .filter(Task.team_id == team_id)
            .all()
        )
    
    def get_all_by_team_id(self, team_id: UUID):
        return (
            self.db.query(Task)
            .filter(Task.team_id == team_id)
            .all()
            )
    
    def get_by_task_id_and_user_id_and_team_id(self, user_id: UUID, team_id: UUID, task_id: UUID):
        return (
            self.db.query(Task)
                .filter(Task.assigned_to == user_id)
                .filter(Task.team_id == team_id)
                .filter(Task.id == task_id)
                .first()
        )
    def create(self, task: TaskCreate, team_id: UUID, created_by: UUID) -> Task:
        db_task = Task(
            team_id=team_id,
            title=task.title,
            description=task.description,
            created_by=created_by,
            assigned_to=task.assigned_to,
            deadline=task.deadline,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def update_status(self, task: Task, new_status: TaskStatus) -> Task:
        task.status = new_status
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def delete_Task(self, task: Task):
        self.db.delete(task)
        self.db.commit()
