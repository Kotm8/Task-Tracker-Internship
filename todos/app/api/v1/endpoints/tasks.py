from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.dependencies.auth import CurrentUserTeamRole, get_current_user_team_role
from app.schemas.task import TaskChangeStatus, TaskCreate, TaskDelete, TaskResponse
from app.services.task_service import TaskService

router = APIRouter()

@router.post("/{team_id}", response_model=TaskResponse)
def create_task(
    team_id: UUID,
    task: TaskCreate,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    current_user: CurrentUserTeamRole = Depends(get_current_user_team_role),
    db: Session = Depends(get_db),
):
    if current_user.role != "pm":
        raise HTTPException(status_code=403, detail="PM access required")

    return TaskService.create_task(
        db,
        task,
        team_id,
        current_user.user_id,
        idempotency_key,
    )
@router.get("/{team_id}/my", response_model=list[TaskResponse])
def get_users_tasks(
    team_id: UUID,
    current_user: CurrentUserTeamRole = Depends(get_current_user_team_role),
    db: Session = Depends(get_db),
):
    
    return TaskService.get_user_tasks(db, team_id, current_user.user_id)

@router.get("/{team_id}", response_model=list[TaskResponse])
def get_all_tasks(
    team_id: UUID,
    current_user: CurrentUserTeamRole = Depends(get_current_user_team_role),
    db: Session = Depends(get_db),
):
    if current_user.role != "pm":
        raise HTTPException(status_code=403, detail="PM access required")

    return TaskService.get_all_team_tasks(db, team_id)

@router.patch("/{team_id}", response_model=TaskResponse)
def change_task_status(
    team_id: UUID,
    task: TaskChangeStatus,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    current_user: CurrentUserTeamRole = Depends(get_current_user_team_role),
    db: Session = Depends(get_db),
):
    return TaskService.change_task_status(db, team_id, current_user.user_id, task, idempotency_key)

@router.delete("/{team_id}/task")
def remove_task(
    team_id: UUID,
    task: TaskDelete,
    current_user: CurrentUserTeamRole = Depends(get_current_user_team_role),
    db: Session = Depends(get_db),
):
    return TaskService.remove_task(db, current_user.user_id, team_id, task.task_id)
