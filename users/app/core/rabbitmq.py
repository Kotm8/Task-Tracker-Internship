import json
import os
import asyncio
from uuid import UUID

import aio_pika
from aio_pika import IncomingMessage, Message
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractQueue
from fastapi import HTTPException

from app.core.permissions import TeamPermission
from app.db.database import SessionLocal
from app.services.team_service import TeamService


RABBITMQ_URL = (os.getenv("RABBITMQ_URL") or "").strip()
RABBITMQ_ROLE_QUEUE = os.getenv("RABBITMQ_ROLE_QUEUE", "role_queue")
RABBITMQ_CONNECT_RETRIES = int(os.getenv("RABBITMQ_CONNECT_RETRIES", "20"))
RABBITMQ_CONNECT_DELAY_SECONDS = float(os.getenv("RABBITMQ_CONNECT_DELAY_SECONDS", "2"))


async def connect_rabbitmq() -> AbstractRobustConnection:
    last_error: Exception | None = None
    for attempt in range(1, RABBITMQ_CONNECT_RETRIES + 1):
        try:
            return await aio_pika.connect_robust(RABBITMQ_URL)
        except Exception as exc:
            last_error = exc
            if attempt == RABBITMQ_CONNECT_RETRIES:
                break
            await asyncio.sleep(RABBITMQ_CONNECT_DELAY_SECONDS)

    if last_error is not None:
        raise last_error
    raise RuntimeError("RabbitMQ connection failed without an error")


class RoleRpcConsumer:
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
            RABBITMQ_ROLE_QUEUE,
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

    async def _on_message(self, message: IncomingMessage) -> None:
        async with message.process():
            response = self._build_response(message.body)

            if not message.reply_to or self._channel is None:
                return

            await self._channel.default_exchange.publish(
                Message(
                    body=json.dumps(response, default=str).encode(),
                    correlation_id=message.correlation_id,
                    content_type="application/json",
                ),
                routing_key=message.reply_to,
            )

    def _build_response(self, body: bytes) -> dict:
        try:
            payload = json.loads(body.decode())
            team_id = UUID(payload["team_id"])
            action = TeamPermission(payload["action"])
            access_token = payload["access_token"]
        except Exception:
            return {
                "error": {
                    "status_code": 400,
                    "detail": "Invalid payload",
                }
            }

        db = SessionLocal()
        try:
            result = TeamService.get_role_in_team(
                db=db,
                access_token=access_token,
                team_id=team_id,
                permission=action,
            )

            return {
                "user_id": str(result.user_id),
                "role": getattr(result.role, "value", result.role),
                "is_allowed": result.is_allowed,
            }

        except HTTPException as exc:
            return {
                "error": {
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                }
            }
        except Exception:
            return {
                "error": {
                    "status_code": 500,
                    "detail": "Role lookup failed",
                }
            }
        finally:
            db.close()


role_rpc_consumer = RoleRpcConsumer()
