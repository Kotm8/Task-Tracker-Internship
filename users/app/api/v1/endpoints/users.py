from fastapi import APIRouter, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.models.users import User
from app.schemas.notification import (
    TaskNotificationRequest,
    TaskNotificationResponse,
)
from app.schemas.user import UserRegister, UserResponse, UserRoleChange
from app.services.notification_service import NotificationService
from app.services.user_service import UserService
router = APIRouter()


@router.get("/whoami", response_model=UserResponse)
def create_user(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserService.get_user_response(db, access_token)

@router.patch("/{user_id}", response_model=UserResponse)
def change_user_role(
    role: UserRoleChange,
    user_id: UUID,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
    ):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if UserService.is_user_admin(db, access_token):
        return UserService.change_user_role(db, role.role, user_id)


@router.post("/notifications/task-email-notification", response_model=TaskNotificationResponse)
def send_task_email(
    notification: TaskNotificationRequest,
    db: Session = Depends(get_db),
):
    return NotificationService.send_task_email(db, notification)

