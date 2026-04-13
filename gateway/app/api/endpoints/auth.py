from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import USER_API_BASE, proxy_request
from app.schemas.auth import TokenPairResponse
from app.schemas.user import UserLogin, UserRegister


router = APIRouter()


@router.post(
    "/register",
    response_model=TokenPairResponse,
    summary="Register a new user",
)
async def register(user: UserRegister, request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/auth/register")


@router.post(
    "/login",
    response_model=TokenPairResponse,
    summary="Log in a user",
)
async def login(user: UserLogin, request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/auth/login")


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    summary="Refresh access and refresh tokens",
)
async def refresh(request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/auth/refresh")


@router.post(
    "/logout",
    summary="Log out the current session",
    responses={200: {"description": "Cookies cleared"}},
)
async def logout(request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/auth/logout")


@router.post(
    "/logout-all",
    summary="Log out all sessions for the current user",
    responses={200: {"description": "All auth cookies cleared"}},
)
async def logout_all(request: Request) -> Response:
    return await proxy_request(request, f"{USER_API_BASE}/api/v1/auth/logout-all")
