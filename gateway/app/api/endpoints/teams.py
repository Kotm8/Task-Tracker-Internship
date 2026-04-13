from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import USER_API_BASE, proxy_request
from app.schemas.team import (
    AddUserToTeam,
    ChangeUserTeamRole,
    DetailResponse,
    TeamCreate,
    TeamCreateResponse,
    TeamMembershipResponse,
    TeamResponse,
    TeamWithRoleResponse,
)


router = APIRouter()


@router.post(
    "/",
    response_model=TeamCreateResponse,
    summary="Create a team",
    description="Requires a global admin session.",
)
async def create_team(team: TeamCreate, request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/team")


@router.post(
    "/{team_id}/members",
    response_model=TeamMembershipResponse,
    summary="Add a user to a team",
    description="Requires a global admin session.",
)
async def add_user_to_team(team_id: str, user: AddUserToTeam, request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/team/{team_id}")


@router.patch(
    "/{team_id}/members/role",
    response_model=TeamMembershipResponse,
    summary="Change a team member's role",
    description="Allowed for global admins and PMs within their own team.",
)
async def change_user_team_role(
    team_id: str,
    user: ChangeUserTeamRole,
    request: Request,
) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/team/{team_id}")


@router.delete(
    "/{team_id}/members/{user_id}",
    response_model=DetailResponse,
    summary="Remove a user from a team",
    description="Allowed for global admins and PMs within their own team.",
)
async def remove_user_from_team(team_id: str, user_id: str, request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/team/{team_id}/{user_id}")


@router.get(
    "/",
    response_model=list[TeamWithRoleResponse],
    summary="Get the current user's teams",
    description="Returns the teams the current user belongs to, including their team role.",
)
async def get_teams(request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/team")


@router.get(
    "/all",
    response_model=list[TeamResponse],
    summary="Get all teams",
    description="Requires a global admin session.",
)
async def get_all_teams(request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/team/all")


@router.get(
    "/{team_id}/members",
    response_model=list[TeamMembershipResponse],
    summary="Get team members",
    description="Allowed for global admins and members of the team.",
)
async def get_teammembers(team_id: str, request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/team/{team_id}/members")
