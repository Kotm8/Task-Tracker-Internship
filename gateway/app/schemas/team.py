from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class TeamCreate(BaseModel):
    name: str


class TeamCreateResponse(BaseModel):
    id: UUID
    name: str


class TeamResponse(BaseModel):
    id: UUID
    name: str


class TeamWithRoleResponse(BaseModel):
    id: UUID
    name: str
    role: Literal["member", "pm", "tl"]


class AddUserToTeam(BaseModel):
    email: EmailStr
    role: Literal["member", "pm", "tl"]


class ChangeUserTeamRole(BaseModel):
    user_id: str
    role: Literal["member", "pm", "tl"]


class TeamMembershipResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: Literal["member", "pm", "tl"]


class DetailResponse(BaseModel):
    detail: str
