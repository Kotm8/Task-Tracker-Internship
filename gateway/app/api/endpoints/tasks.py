from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import Response

from app.core.proxy import TODO_API_BASE, proxy_request
from app.schemas.task import PaginatedTaskResponse, TaskChangeStatus, TaskCreate, TaskDelete, TaskResponse


router = APIRouter()


@router.post(
    "/{team_id}",
    response_model=TaskResponse,
    summary="Create a task",
    description="Allowed only for PMs within the target team.",
)
async def create_task(
    team_id: UUID,
    task: TaskCreate,
    request: Request,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
) -> Response:
    return await proxy_request(request, f"{TODO_API_BASE}/api/v1/tasks/{team_id}")


@router.get(
    "/{team_id}/my",
    response_model=PaginatedTaskResponse,
    summary="Get my tasks in a team",
    description="Returns the tasks assigned to the current user within the team.",
)
async def get_my_tasks(
    team_id: UUID,
    request: Request,
    status: Literal["todo", "in_progress", "review", "done", "cancelled"] | None = Query(
        None,
        description="Filter by task status: `todo`, `in_progress`, `review`, `done`, or `cancelled`.",
    ),
    deadline: Literal["before", "after"] | None = Query(
        None,
        description="Filter tasks by deadline relative to now: `before` or `after`.",
    ),
    sort: Literal["deadline", "created_at", "updated_at"] | None = Query(
        None,
        description="Sort field. Available values: `deadline`, `created_at`, `updated_at`.",
    ),
    direction: Literal["asc", "desc"] = Query(
        "asc",
        description="Sort direction: `asc` or `desc`.",
    ),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> Response:
    return await proxy_request(request, f"{TODO_API_BASE}/api/v1/tasks/{team_id}/my")


@router.get(
    "/{team_id}",
    response_model=PaginatedTaskResponse,
    summary="Get all team tasks",
    description="Allowed only for PMs within the target team.",
)
async def get_all_tasks(
    team_id: UUID, 
    request: Request,
    status: Literal["todo", "in_progress", "review", "done", "cancelled"] | None = Query(
        None,
        description="Filter by task status: `todo`, `in_progress`, `review`, `done`, or `cancelled`.",
    ),
    deadline: Literal["before", "after"] | None = Query(
        None,
        description="Filter tasks by deadline relative to now: `before` or `after`.",
    ),
    sort: Literal["deadline", "created_at", "updated_at"] | None = Query(
        None,
        description="Sort field. Available values: `deadline`, `created_at`, `updated_at`.",
    ),
    direction: Literal["asc", "desc"] = Query(
        "asc",
        description="Sort direction: `asc` or `desc`.",
    ),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> Response:
    return await proxy_request(request, f"{TODO_API_BASE}/api/v1/tasks/{team_id}")


@router.patch(
    "/{team_id}",
    response_model=TaskResponse,
    summary="Change task status",
    description="Allowed for a team member on their own assigned task.",
)
async def change_task_status(
    team_id: UUID,
    task: TaskChangeStatus,
    request: Request,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
) -> Response:
    return await proxy_request(request, f"{TODO_API_BASE}/api/v1/tasks/{team_id}")


@router.delete(
    "/{team_id}/task",
    response_model=TaskResponse,
    summary="delete a task",
    description="Allowed for a team member on their own assigned task.",
)
async def remove_task(team_id: UUID, task: TaskDelete, request: Request) -> Response:
    return await proxy_request(request, f"{TODO_API_BASE}/api/v1/tasks/{team_id}/task")
