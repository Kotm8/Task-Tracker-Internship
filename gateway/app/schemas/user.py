from uuid import UUID
from typing import Literal

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRoleChange(BaseModel):
    role: Literal["user", "admin"]


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: Literal["user", "admin"]
