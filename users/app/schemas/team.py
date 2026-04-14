from uuid import UUID
from pydantic import BaseModel
from app.core.enums import TeamRole


class TeamCreate(BaseModel):
    name: str

class TeamResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True

class TeamWithRoleResponse(BaseModel):
    id: UUID
    name: str
    role: TeamRole

class AddUserToTeam(BaseModel):
    email: str
    role: TeamRole

class ChangeUserTeamRole(BaseModel):
    user_id: UUID
    role: TeamRole

class TeamMembershipResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: TeamRole

class RoleResponse(BaseModel):
    user_id: UUID
    role: TeamRole
    is_allowed: bool