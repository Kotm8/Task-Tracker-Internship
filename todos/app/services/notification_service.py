import httpx

from app.core.config import USER_SERVICE_URL
from app.core.task_events import TaskEventEnvelope
from app.repositories.integration_event_repository import IntegrationEventRepository


class NotificationService:
    @staticmethod
    def handle_event(repo: IntegrationEventRepository, event: TaskEventEnvelope) -> None:
        if not event.payload.get("assigned_to"):
            return

        log_entry = repo.get_notification_log_by_event_id(event.event_id)
        if log_entry is None:
            log_entry = repo.create_notification_log(event)

        repo.update_notification_log_status(log_entry, "pending_delivery")

        try:
            NotificationService._send_task_notification(event)
        except Exception:
            repo.update_notification_log_status(log_entry, "failed")
            raise

        repo.update_notification_log_status(log_entry, "sent")

    @staticmethod
    def _send_task_notification(event):
        response = httpx.post(
            f"{USER_SERVICE_URL}/api/v1/users/notifications/task-email-notification",
            json={
                "user_id": event.payload["assigned_to"],
                "task_id": event.payload["task_id"],
                "team_id": event.payload["team_id"],
                "event_type": event.event_type,
                "title": event.payload["title"],
                "description": event.payload.get("description"),
                "deadline": event.payload.get("deadline"),
                "status": event.payload.get("status"),
                "old_status": event.payload.get("old_status"),
                "new_status": event.payload.get("new_status"),
            },
            timeout=10.0,
        )
        response.raise_for_status()
