from fastapi import APIRouter, Cookie, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.dependencies.auth import CurrentUserTeamRole, get_current_user_team_role
from app.schemas.task import TaskChangeStatus, TaskCreate, TaskDelete, TaskResponse
from app.services.task_service import TaskService
from app.core.permissions import TeamPermission

router = APIRouter()

@router.post("/{team_id}", response_model=TaskResponse)
async def create_task(
    team_id: UUID,
    task: TaskCreate,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    current_user = await get_current_user_team_role(
        team_id=str(team_id),
        action=TeamPermission.CREATE_TASK,
        access_token=access_token,
    )

    if current_user.is_allowed:
        return TaskService.create_task(
            db,
            task,
            team_id,
            current_user.user_id,
            idempotency_key,
        )
    else:
        raise HTTPException(status_code=403, detail="insufficient permissions")
    
@router.get("/{team_id}/my", response_model=list[TaskResponse])
async def get_users_tasks(
    team_id: UUID,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    current_user = await get_current_user_team_role(
        team_id=str(team_id),
        action=TeamPermission.VIEW_USER_TASKS,
        access_token=access_token,
    )

    if current_user.is_allowed:
        return TaskService.get_user_tasks(db, team_id, current_user.user_id)
    else:
        raise HTTPException(status_code=403, detail="insufficient permissions")

@router.get("/{team_id}", response_model=list[TaskResponse])
async def get_all_tasks(
    team_id: UUID,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    current_user = await get_current_user_team_role(
        team_id=str(team_id),
        action=TeamPermission.VIEW_ALL_TASKS,
        access_token=access_token,
    )

    if current_user.is_allowed:
        return TaskService.get_all_team_tasks(db, team_id)
    else:
        raise HTTPException(status_code=403, detail="insufficient permissions")

@router.patch("/{team_id}", response_model=TaskResponse)
async def change_task_status(
    team_id: UUID,
    task: TaskChangeStatus,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    current_user = await get_current_user_team_role(
        team_id=str(team_id),
        action=TeamPermission.CHANGE_TASK_STATUS,
        access_token=access_token,
    )
    
    if current_user.is_allowed:
       return TaskService.change_task_status(db, team_id, current_user.user_id, task, idempotency_key)
    else:
        raise HTTPException(status_code=403, detail="insufficient permissions")

@router.delete("/{team_id}/task")
async def remove_task(
    team_id: UUID,
    task: TaskDelete,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    current_user = await get_current_user_team_role(
        team_id=str(team_id),
        action=TeamPermission.DELETE_TASK,
        access_token=access_token,
    )
    
    if current_user.is_allowed:
        return TaskService.remove_task(db, current_user.user_id, team_id, task.task_id)
    else:
        raise HTTPException(status_code=403, detail="insufficient permissions")
