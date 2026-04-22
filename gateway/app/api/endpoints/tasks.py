from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import Response

from app.core.proxy import TODO_API_BASE, proxy_stream_request
from app.core.rabbitmq import RABBITMQ_TASK_QUEUE, task_rpc_client
from app.schemas.task import PaginatedTaskResponse, TaskChangeStatus, TaskCreate, TaskDelete, TaskResponse
from app.core.enums import TeamPermission

router = APIRouter()


async def _call_todo_rpc(payload: dict) -> dict:
    try:
        response = await task_rpc_client.call(
            RABBITMQ_TASK_QUEUE,
            payload,
        )
    except TimeoutError:
        raise HTTPException(status_code=503, detail="Todo service unavailable")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Todo service unavailable")

    error = response.get("error")
    if error:
        raise HTTPException(
            status_code=error.get("status_code", 502),
            detail=error.get("detail", "Todo service error"),
        )

    return response["data"]


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
) -> TaskResponse:
    return await _call_todo_rpc(
        {
            "action": TeamPermission.CREATE_TASK,
            "team_id": str(team_id),
            "task": task.model_dump(mode="json"),
            "idempotency_key": str(idempotency_key),
            "access_token": request.cookies.get("access_token"),
        }
    )


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
) -> PaginatedTaskResponse:
    return await _call_todo_rpc(
        {
            "action":  TeamPermission.VIEW_USER_TASKS,
            "team_id": str(team_id),
            "access_token": request.cookies.get("access_token"),
            "filters": {
                "status": status,
                "deadline": deadline,
                "sort": sort,
                "direction": direction,
                "limit": limit,
                "page": page,
            },
        }
    )


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
) -> PaginatedTaskResponse:
    return await _call_todo_rpc(
        {
            "action":  TeamPermission.VIEW_ALL_TASKS,
            "team_id": str(team_id),
            "access_token": request.cookies.get("access_token"),
            "filters": {
                "status": status,
                "deadline": deadline,
                "sort": sort,
                "direction": direction,
                "limit": limit,
                "page": page,
            },
        }
    )


@router.get(
    "/{team_id}/audit.csv",
    summary="Download team audit CSV",
    description="Exports audit events for the team as either a raw or aggregated CSV file.",
)
async def export_team_audit(
    team_id: UUID,
    request: Request,
    mode: Literal["raw", "aggregated"] = Query("aggregated"),
) -> Response:
    return await proxy_stream_request(
        request,
        f"{TODO_API_BASE}/api/v1/audit/{team_id}/audit.csv",
    )


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
) -> TaskResponse:
    return await _call_todo_rpc(
        {
            "action":  TeamPermission.CHANGE_TASK_STATUS,
            "team_id": str(team_id),
            "task": task.model_dump(mode="json"),
            "idempotency_key": str(idempotency_key),
            "access_token": request.cookies.get("access_token"),
        }
    )


@router.delete(
    "/{team_id}/task",
    response_model=TaskResponse,
    summary="delete a task",
    description="Allowed for a team member on their own assigned task.",
)
async def remove_task(team_id: UUID, task: TaskDelete, request: Request) -> TaskResponse:
    return await _call_todo_rpc(
        {
            "action":  TeamPermission.DELETE_TASK,
            "team_id": str(team_id),
            "task": task.model_dump(mode="json"),
            "access_token": request.cookies.get("access_token"),
        }
    )
