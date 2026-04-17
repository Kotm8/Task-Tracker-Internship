from typing import Literal
from uuid import UUID

from fastapi import Cookie, HTTPException
from pydantic import BaseModel, ValidationError

from app.core.permissions import TeamPermission
from app.core.rabbitmq import RABBITMQ_ROLE_QUEUE, role_rpc_client


class CurrentUserTeamRole(BaseModel):
    user_id: UUID
    role: Literal["member", "pm", "tl"]
    is_allowed: bool


def require_team_permission(action: TeamPermission):
    async def dependency(
        team_id: UUID,
        access_token: str | None = Cookie(None),
    ):
        current_user = await get_current_user_team_role(
            team_id=str(team_id),
            action=action,
            access_token=access_token,
        )

        if not current_user.is_allowed:
            raise HTTPException(status_code=403, detail="insufficient permissions")

        return current_user

    return dependency

async def get_current_user_team_role(
    team_id: str,
    action: TeamPermission,
    access_token: str | None = Cookie(None),
) -> CurrentUserTeamRole:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = await role_rpc_client.call(
            RABBITMQ_ROLE_QUEUE,
            {
                "team_id": team_id,
                "action": action.value,
                "access_token": access_token,
            },
        )
        error = payload.get("error")
        if error:
            raise HTTPException(
                status_code=error.get("status_code", 502),
                detail=error.get("detail", "User service error"),
            )

        return CurrentUserTeamRole.model_validate(payload)
    except ValidationError:
        raise HTTPException(status_code=502, detail="Invalid user service payload")
    except TimeoutError:
        raise HTTPException(status_code=503, detail="User service unavailable")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="User service unavailable")
