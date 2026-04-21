import asyncio
import logging

from app.core.config import (
    TASK_EVENT_PUBLISH_BATCH_SIZE,
    TASK_EVENT_PUBLISH_INTERVAL_SECONDS,
)
from app.core.event_bus import (
    build_event_message,
    connect_rabbitmq,
    declare_task_event_topology,
)
from app.core.task_events import TaskEventEnvelope
from app.db.database import SessionLocal
from app.repositories.outbox_repository import OutboxRepository


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


async def publish_once(exchange) -> None:
    with SessionLocal() as db:
        repo = OutboxRepository(db)
        events = repo.lock_batch(TASK_EVENT_PUBLISH_BATCH_SIZE)

        for db_event in events:
            envelope = TaskEventEnvelope(
                event_id=db_event.event_id,
                event_type=db_event.event_type,
                occurred_at=db_event.occurred_at,
                producer=db_event.producer,
                correlation_id=db_event.correlation_id,
                version=db_event.version,
                payload=db_event.payload,
            )
            try:
                await exchange.publish(
                    build_event_message(envelope),
                    routing_key=db_event.routing_key,
                )
                repo.mark_published(db_event)
                db.commit()
            except Exception as exc:
                repo.mark_failed(db_event, str(exc))
                db.commit()
                logger.exception("Failed to publish outbox event %s", db_event.event_id)


async def main() -> None:
    connection = await connect_rabbitmq()
    channel = await connection.channel()
    exchange = await declare_task_event_topology(channel)

    try:
        while True:
            await publish_once(exchange)
            await asyncio.sleep(TASK_EVENT_PUBLISH_INTERVAL_SECONDS)
    finally:
        await channel.close()
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
