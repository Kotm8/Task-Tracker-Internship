import asyncio
import logging

from app.core.event_bus import (
    TASK_EVENTS_NOTIFICATIONS_DLQ_QUEUE,
    TASK_EVENTS_NOTIFICATIONS_QUEUE,
    TASK_EVENTS_NOTIFICATIONS_RETRY_QUEUE,
    TaskEventConsumerWorker,
)
from app.core.task_events import TaskEventEnvelope
from app.repositories.integration_event_repository import IntegrationEventRepository
from app.services.notification_service import NotificationService


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def handle_event(repo: IntegrationEventRepository, event: TaskEventEnvelope) -> None:
    NotificationService.handle_event(repo, event)


async def main() -> None:
    worker = TaskEventConsumerWorker(
        consumer_name="notification-worker",
        queue_name=TASK_EVENTS_NOTIFICATIONS_QUEUE,
        retry_queue_name=TASK_EVENTS_NOTIFICATIONS_RETRY_QUEUE,
        dlq_queue_name=TASK_EVENTS_NOTIFICATIONS_DLQ_QUEUE,
        handle_event=handle_event,
    )
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
