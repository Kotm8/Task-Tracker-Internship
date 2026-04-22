import asyncio
import json

from aio_pika import DeliveryMode, IncomingMessage, Message
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractQueue
from pydantic import ValidationError

from app.core import config
from app.core.rabbitmq import connect_rabbitmq
from app.db.database import SessionLocal
from app.services.notification_service import NotificationService
from app.schemas.notification import TaskEventEnvelope, TaskNotificationRequest

def build_raw_message(
    body: bytes,
    *,
    headers: dict | None = None,
    correlation_id: str | None = None,
    message_id: str | None = None,
) -> Message:
    return Message(
        body=body,
        content_type="application/json",
        delivery_mode=DeliveryMode.PERSISTENT,
        headers=headers or {},
        correlation_id=correlation_id,
        message_id=message_id,
    )

class NotificationWorker:
    def __init__(self) -> None:
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None
        self._queue: AbstractQueue | None = None
        self._consumer_tag: str | None = None

    async def start(self) -> None:
        self._connection = await connect_rabbitmq()
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        self._queue = await self._channel.declare_queue(
            config.TASK_EVENTS_NOTIFICATIONS_QUEUE,
            durable=True,
        )
        self._consumer_tag = await self._queue.consume(self._on_message)

    async def stop(self) -> None:
        if self._queue and self._consumer_tag:
            try:
                await self._queue.cancel(self._consumer_tag)
            except Exception:
                pass

        if self._channel and not self._channel.is_closed:
            try:
                await self._channel.close()
            except Exception:
                pass

        if self._connection and not self._connection.is_closed:
            try:
                await self._connection.close()
            except Exception:
                pass

        self._connection = None
        self._channel = None
        self._queue = None
        self._consumer_tag = None

    async def run_forever(self) -> None:
        await self.start()
        try:
            await asyncio.Future()
        finally:
            await self.stop()

    async def _on_message(self, message: IncomingMessage) -> None:
        try:
            raw_payload = json.loads(message.body.decode())
            event = TaskEventEnvelope.model_validate(raw_payload)

            task_payload = event.payload
            assigned_to = task_payload.get("assigned_to")
            if not assigned_to:
                await message.ack()
                return

            notification = TaskNotificationRequest(
                user_id=assigned_to,
                task_id=task_payload["task_id"],
                team_id=task_payload["team_id"],
                event_type=event.event_type,
                title=task_payload["title"],
                description=task_payload.get("description"),
                deadline=task_payload.get("deadline"),
                status=task_payload.get("status"),
                old_status=task_payload.get("old_status"),
                new_status=task_payload.get("new_status"),
            )

            with SessionLocal() as db:
                NotificationService.send_task_email(db, notification)

            await message.ack()

        except (json.JSONDecodeError, ValidationError, KeyError) as exc:
            await self._route_failed_message(message, exc)

        except Exception as exc:
            await self._route_failed_message(message, exc)

    async def _route_failed_message(self, message: IncomingMessage, exc: Exception) -> None:
        if self._channel is None:
            await message.nack(requeue=True)
            return
    
        retry_count = int((message.headers or {}).get("x-retry-count", 0))
        headers = dict(message.headers or {})
        headers["x-retry-count"] = retry_count + 1
        headers["x-last-error"] = str(exc)[:500]
    
        target_queue = (
            config.TASK_EVENTS_NOTIFICATIONS_RETRY_QUEUE
            if retry_count < config.TASK_EVENT_MAX_RETRIES
            else config.TASK_EVENTS_NOTIFICATIONS_DLQ_QUEUE
        )
    
        await self._channel.default_exchange.publish(
            build_raw_message(
                message.body,
                headers=headers,
                correlation_id=message.correlation_id,
                message_id=message.message_id,
            ),
            routing_key=target_queue,
        )
        await message.ack()



async def main() -> None:
    worker = NotificationWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
