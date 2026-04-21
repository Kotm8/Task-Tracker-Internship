import asyncio
import logging

from app.core.event_bus import (
    TASK_EVENTS_AUDIT_DLQ_QUEUE,
    TASK_EVENTS_AUDIT_QUEUE,
    TASK_EVENTS_AUDIT_RETRY_QUEUE,
    TaskEventConsumerWorker,
)
from app.core.task_events import TaskEventEnvelope
from app.repositories.integration_event_repository import IntegrationEventRepository


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def handle_event(repo: IntegrationEventRepository, event: TaskEventEnvelope) -> None:
    repo.create_audit_log(event)


async def main() -> None:
    worker = TaskEventConsumerWorker(
        consumer_name="audit-worker",
        queue_name=TASK_EVENTS_AUDIT_QUEUE,
        retry_queue_name=TASK_EVENTS_AUDIT_RETRY_QUEUE,
        dlq_queue_name=TASK_EVENTS_AUDIT_DLQ_QUEUE,
        handle_event=handle_event,
    )
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
