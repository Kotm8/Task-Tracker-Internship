from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import USER_API_BASE, proxy_request
from app.schemas.user import UserResponse, UserRoleChange


router = APIRouter()


@router.get(
    "/whoami",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
async def whoami(request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/users/whoami")


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Change a user's global role",
    description="Requires a global admin session. Updates the target user's system role.",
)
async def change_user_role(user_id: str, role: UserRoleChange, request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/users/{user_id}")
