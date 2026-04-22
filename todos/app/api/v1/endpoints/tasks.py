from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.dependencies.auth import require_team_permission
from app.schemas.task import PaginatedTaskResponse, TaskChangeStatus, TaskCreate, TaskDelete, TaskResponse
from app.services.task_service import TaskService
from app.core.permissions import TeamPermission


router = APIRouter()

@router.post("/{team_id}", response_model=TaskResponse)
async def create_task(
    team_id: UUID,
    task: TaskCreate,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user=Depends(require_team_permission(TeamPermission.CREATE_TASK)),
):

    return TaskService.create_task(
        db,
        task,
        team_id,
        current_user.user_id,
        idempotency_key,
    )

@router.get("/{team_id}/my", response_model=PaginatedTaskResponse)
async def get_users_tasks(
    team_id: UUID,
    status: str | None = Query(None),
    deadline: str | None = Query(None),
    sort: str | None = Query(None),
    direction: str | None = Query("asc"), 
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_team_permission(TeamPermission.VIEW_USER_TASKS)),
):
    
    return TaskService.get_user_tasks(
        db=db, 
        user_id=current_user.user_id,
        team_id=team_id, 
        status=status,
        deadline=deadline,
        direction=direction,
        sort=sort,
        limit=limit,
        page=page,
        )

@router.get("/{team_id}", response_model=PaginatedTaskResponse)
async def get_all_tasks(
    team_id: UUID,
    status: str | None = Query(None),
    deadline: str | None = Query(None),
    sort: str | None = Query(None),
    direction: str | None = Query("asc"), 
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_team_permission(TeamPermission.VIEW_ALL_TASKS)),
):
        
    return TaskService.get_all_team_tasks(
        db=db, 
        team_id=team_id, 
        status=status,
        deadline=deadline,
        direction=direction,
        sort=sort,
        limit=limit,
        page=page,
        )

@router.patch("/{team_id}", response_model=TaskResponse)
async def change_task_status(
    team_id: UUID,
    task: TaskChangeStatus,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user=Depends(require_team_permission(TeamPermission.CHANGE_TASK_STATUS)),
):
       
    return TaskService.change_task_status(db, team_id, current_user.user_id, task, idempotency_key)

@router.delete("/{team_id}/task")
async def remove_task(
    team_id: UUID,
    task: TaskDelete,
    db: Session = Depends(get_db),
    current_user=Depends(require_team_permission(TeamPermission.DELETE_TASK)),
):
    
    return TaskService.remove_task(db, current_user.user_id, team_id, task.task_id)


