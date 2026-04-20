from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import TaskStatus
from app.models.tasks import Task
from app.schemas.task import TaskCreate


class TaskRepository:
    SORT_MAP = {
        "deadline": Task.deadline,
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
    }

    def __init__(self, db: Session):
        self.db = db

    def get_user_tasks(
        self,
        team_id: UUID,
        user_id: UUID | None = None,
        status=None,
        deadline=None,
        sort=None,
        direction="asc",
        limit=10,
        page=1,
    ):
        conditions = [Task.team_id == team_id]

        if user_id is not None:
            conditions.append(Task.assigned_to == user_id)

        if status:
            conditions.append(Task.status == status)

        now = datetime.now(timezone.utc)

        if deadline == "before":
            conditions.append(Task.deadline < now)
        elif deadline == "after":
            conditions.append(Task.deadline >= now)

        total_stmt = select(func.count()).select_from(Task).where(*conditions)
        total = self.db.scalar(total_stmt) or 0

        stmt = select(Task).where(*conditions)

        if sort in self.SORT_MAP:
            column = self.SORT_MAP[sort]
            stmt = stmt.order_by(column.desc() if direction == "desc" else column.asc())

        offset = (page - 1) * limit
        items = self.db.scalars(stmt.offset(offset).limit(limit)).all()

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
        }

    def get_by_task_id_and_user_id_and_team_id(self, user_id: UUID, team_id: UUID, task_id: UUID):
        stmt = (
            select(Task)
            .where(Task.assigned_to == user_id)
            .where(Task.team_id == team_id)
            .where(Task.id == task_id)
        )
        return self.db.scalar(stmt)

    def get_by_task_id_and_team_id(self, team_id: UUID, task_id: UUID):
        stmt = (
            select(Task)
            .where(Task.team_id == team_id)
            .where(Task.id == task_id)
        )
        return self.db.scalar(stmt)

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
        self.db.flush()
        self.db.refresh(db_task)
        return db_task

    def update_status(self, task: Task, new_status: TaskStatus) -> Task:
        task.status = new_status
        self.db.flush()
        self.db.refresh(task)
        return task

    def delete_Task(self, task: Task):
        self.db.delete(task)
