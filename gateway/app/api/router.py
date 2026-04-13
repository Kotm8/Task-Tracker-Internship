from fastapi import APIRouter

from app.api.endpoints import auth, tasks, teams, users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/api/v1/users", tags=["users"])
api_router.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
api_router.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
