import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.repositories.team_repository import TeamRepository
from app.schemas.notification import TaskNotificationRequest


logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def send_task_email(
        db: Session,
        notification: TaskNotificationRequest,
    ) -> None:
        user_repo = UserRepository(db)
        db_user = user_repo.get_one(user_id=notification.user_id)
        team_repo = TeamRepository(db)
        db_team = team_repo.get_one(team_id=notification.team_id)
        if not db_user :
            raise HTTPException(status_code=404, detail="User not found")
        if not db_team :
            raise HTTPException(status_code=404, detail="Team not found")

        message = NotificationService._build_mock_message(notification, db_user.email, db_team.name)
        print(message)
    
    def _build_mock_message(notification: TaskNotificationRequest, email: str, team_name: str) -> str:
        if notification.event_type == "task.created":
            return f"Mock task created email sent to {email} for task {notification.title} in team {team_name}"

        if notification.event_type == "task.status_changed":
            return (
                f"Mock task status changed email sent to {email} for task {notification.title} "
                f"in team {team_name}: {notification.old_status} -> {notification.new_status}"
            )

        if notification.event_type == "task.deleted":
            return f"Mock task deleted email sent to {email} for task {notification.title} in team {team_name}"

        return f"Mock task notification {notification.event_type} sent to {email} for task {notification.title} in team {team_name}"
