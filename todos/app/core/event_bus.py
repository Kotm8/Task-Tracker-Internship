from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable
from uuid import UUID

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, IncomingMessage, Message
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractRobustExchange, AbstractRobustQueue

from app.core.config import (
    RABBITMQ_CONNECT_DELAY_SECONDS,
    RABBITMQ_CONNECT_RETRIES,
    RABBITMQ_URL,
    TASK_EVENTS_AUDIT_DLQ_QUEUE,
    TASK_EVENTS_AUDIT_QUEUE,
    TASK_EVENTS_AUDIT_RETRY_QUEUE,
    TASK_EVENTS_EXCHANGE,
    TASK_EVENTS_NOTIFICATIONS_DLQ_QUEUE,
    TASK_EVENTS_NOTIFICATIONS_QUEUE,
    TASK_EVENTS_NOTIFICATIONS_RETRY_QUEUE,
    TASK_EVENT_MAX_RETRIES,
    TASK_EVENT_RETRY_DELAY_MS,
)
from app.core.task_events import TaskEventEnvelope
from app.db.database import SessionLocal
from app.repositories.integration_event_repository import IntegrationEventRepository


logger = logging.getLogger(__name__)


async def connect_rabbitmq() -> AbstractRobustConnection:
    last_error: Exception | None = None
    for attempt in range(1, RABBITMQ_CONNECT_RETRIES + 1):
        try:
            return await aio_pika.connect_robust((RABBITMQ_URL or "").strip())
        except Exception as exc:
            last_error = exc
            if attempt == RABBITMQ_CONNECT_RETRIES:
                break
            await asyncio.sleep(RABBITMQ_CONNECT_DELAY_SECONDS)

    if last_error is not None:
        raise last_error
    raise RuntimeError("RabbitMQ connection failed without an error")


def build_event_message(event: TaskEventEnvelope, headers: dict | None = None) -> Message:
    return Message(
        body=json.dumps(event.model_dump(mode="json"), default=str).encode(),
        content_type="application/json",
        delivery_mode=DeliveryMode.PERSISTENT,
        message_id=str(event.event_id),
        correlation_id=str(event.correlation_id) if event.correlation_id else None,
        headers=headers or {},
    )


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


def parse_event(message: IncomingMessage) -> TaskEventEnvelope:
    return TaskEventEnvelope.model_validate_json(message.body.decode())


async def declare_task_event_topology(channel: AbstractRobustChannel) -> AbstractRobustExchange:
    exchange = await channel.declare_exchange(
        TASK_EVENTS_EXCHANGE,
        ExchangeType.TOPIC,
        durable=True,
    )

    audit_queue = await channel.declare_queue(TASK_EVENTS_AUDIT_QUEUE, durable=True)
    await audit_queue.bind(exchange, routing_key="task.*")

    await channel.declare_queue(
        TASK_EVENTS_AUDIT_RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": TASK_EVENT_RETRY_DELAY_MS,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": TASK_EVENTS_AUDIT_QUEUE,
        },
    )
    await channel.declare_queue(TASK_EVENTS_AUDIT_DLQ_QUEUE, durable=True)

    notifications_queue = await channel.declare_queue(TASK_EVENTS_NOTIFICATIONS_QUEUE, durable=True)
    for routing_key in ("task.created", "task.status_changed", "task.deleted"):
        await notifications_queue.bind(exchange, routing_key=routing_key)

    await channel.declare_queue(
        TASK_EVENTS_NOTIFICATIONS_RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": TASK_EVENT_RETRY_DELAY_MS,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": TASK_EVENTS_NOTIFICATIONS_QUEUE,
        },
    )
    await channel.declare_queue(TASK_EVENTS_NOTIFICATIONS_DLQ_QUEUE, durable=True)

    return exchange


class TaskEventConsumerWorker:
    def __init__(
        self,
        *,
        consumer_name: str,
        queue_name: str,
        retry_queue_name: str,
        dlq_queue_name: str,
        handle_event: Callable[[IntegrationEventRepository, TaskEventEnvelope], None],
    ) -> None:
        self.consumer_name = consumer_name
        self.queue_name = queue_name
        self.retry_queue_name = retry_queue_name
        self.dlq_queue_name = dlq_queue_name
        self.handle_event = handle_event
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None
        self._queue: AbstractRobustQueue | None = None

    async def start(self) -> None:
        self._connection = await connect_rabbitmq()
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        await declare_task_event_topology(self._channel)
        self._queue = await self._channel.declare_queue(self.queue_name, durable=True)
        await self._queue.consume(self._on_message)

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def run_forever(self) -> None:
        await self.start()
        try:
            await asyncio.Future()
        finally:
            await self.close()

    async def _on_message(self, message: IncomingMessage) -> None:
        event: TaskEventEnvelope | None = None
        try:
            event = parse_event(message)
            with SessionLocal() as db:
                repo = IntegrationEventRepository(db)
                if repo.is_processed(self.consumer_name, event.event_id):
                    await message.ack()
                    return

                self.handle_event(repo, event)
                repo.mark_processed(self.consumer_name, event.event_id)
                db.commit()

            await message.ack()
        except Exception as exc:
            self._store_processing_error(event, exc)
            logger.exception("%s failed to process task event", self.consumer_name)
            await self._route_failed_message(message, exc)

    def _store_processing_error(self, event: TaskEventEnvelope | None, exc: Exception) -> None:
        try:
            team_id: UUID | None = None
            if event is not None and event.payload.get("team_id"):
                try:
                    team_id = UUID(str(event.payload["team_id"]))
                except (ValueError, TypeError):
                    team_id = None

            with SessionLocal() as db:
                repo = IntegrationEventRepository(db)
                repo.create_processing_error_log(
                    consumer_name=self.consumer_name,
                    event_id=event.event_id if event is not None else None,
                    event_type=event.event_type if event is not None else None,
                    team_id=team_id,
                    payload=event.payload if event is not None else None,
                    error_type=type(exc).__name__,
                    error_text=str(exc)[:1000],
                )
                db.commit()
        except Exception:
            logger.exception("%s failed to persist processing error log", self.consumer_name)

    async def _route_failed_message(self, message: IncomingMessage, exc: Exception) -> None:
        if self._channel is None:
            await message.nack(requeue=True)
            return

        retry_count = int((message.headers or {}).get("x-retry-count", 0))
        headers = dict(message.headers or {})
        headers["x-retry-count"] = retry_count + 1
        headers["x-last-error"] = str(exc)[:500]

        target_queue = self.retry_queue_name if retry_count < TASK_EVENT_MAX_RETRIES else self.dlq_queue_name
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
