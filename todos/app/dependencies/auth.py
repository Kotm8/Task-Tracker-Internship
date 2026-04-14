from typing import Literal
from uuid import UUID

import httpx
from fastapi import Cookie, HTTPException
from pydantic import BaseModel, ValidationError
import os 
from dotenv import load_dotenv

from app.core.permissions import TeamPermission

load_dotenv()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")


class CurrentUserTeamRole(BaseModel):
    user_id: UUID
    role: Literal["member", "pm", "tl"]
    is_allowed: bool


async def get_current_user_id(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/v1/users/whoami",
                cookies={"access_token": access_token},
                timeout=5.0
            )

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = response.json()
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user payload")
        return user_id

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="User service unavailable")
    
async def get_current_user_team_role(
    team_id: str,
    action: TeamPermission,
    access_token: str = Cookie(None),
) -> CurrentUserTeamRole:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/v1/team/{team_id}/getrole/{action}",
                cookies={"access_token": access_token},
                timeout=5.0,
            )

        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid token")

        if response.status_code in {403, 404}:
            detail = response.json().get("detail", "User is not in this team")
            raise HTTPException(status_code=response.status_code, detail=detail)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="User service error")

        payload = response.json()

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid user payload")

        return CurrentUserTeamRole.model_validate(payload)
    except ValidationError:
        raise HTTPException(status_code=502, detail="Invalid user service payload")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="User service unavailable")
