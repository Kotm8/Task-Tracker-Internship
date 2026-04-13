from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.core.enums import SystemRole


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRoleChange(BaseModel):
    role: SystemRole

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: SystemRole = Field(validation_alias="system_role")

    class Config:
        from_attributes = True
