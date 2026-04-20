import asyncio
import json
import logging
import os
from urllib.parse import quote
from uuid import UUID, uuid4

import aio_pika
from aio_pika import DeliveryMode, IncomingMessage, Message
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractQueue
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.permissions import TeamPermission
from app.db.database import SessionLocal
from app.schemas.task import (
    PaginatedTaskResponse,
    TaskChangeStatus,
    TaskCreate,
    TaskDelete,
    TaskResponse,
)
from app.services.task_service import TaskService


RABBITMQ_ROLE_QUEUE = os.getenv("RABBITMQ_ROLE_QUEUE", "role_queue")
RABBITMQ_TASK_QUEUE = os.getenv("RABBITMQ_TASK_QUEUE", "task_queue")

RABBITMQ_URL = (os.getenv("RABBITMQ_URL") or "").strip()
RABBITMQ_CONNECT_RETRIES = int(os.getenv("RABBITMQ_CONNECT_RETRIES", "20"))
RABBITMQ_CONNECT_DELAY_SECONDS = float(os.getenv("RABBITMQ_CONNECT_DELAY_SECONDS", "2"))

logger = logging.getLogger(__name__)



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


class RoleRpcClient:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None
        self._callback_queue: AbstractQueue | None = None
        self._consumer_tag: str | None = None
        self._responses: dict[str, asyncio.Future[bytes]] = {}

    async def connect(self) -> None:
        async with self._lock:
            if self._connection and not self._connection.is_closed:
                return

            self._connection = await connect_rabbitmq()
            self._channel = await self._connection.channel()
            self._callback_queue = await self._channel.declare_queue(
                "",
                exclusive=True,
                auto_delete=True,
            )
            self._consumer_tag = await self._callback_queue.consume(
                self._on_response,
                no_ack=True,
            )

    async def close(self) -> None:
        async with self._lock:
            if self._callback_queue and self._consumer_tag:
                try:
                    await self._callback_queue.cancel(self._consumer_tag)
                except Exception:
                    pass

            for future in self._responses.values():
                if not future.done():
                    future.cancel()
            self._responses.clear()

            if self._channel and not self._channel.is_closed:
                await self._channel.close()

            if self._connection and not self._connection.is_closed:
                await self._connection.close()

            self._connection = None
            self._channel = None
            self._callback_queue = None
            self._consumer_tag = None

    async def _on_response(self, message: IncomingMessage) -> None:
        if message.correlation_id in self._responses:
            future = self._responses.pop(message.correlation_id)
            if not future.done():
                future.set_result(message.body)

    async def call(self, queue_name: str, payload: dict, timeout: float = 5.0) -> dict:
        await self.connect()

        if self._channel is None or self._callback_queue is None:
            raise RuntimeError("Role RPC client is not connected")

        correlation_id = str(uuid4())
        future = asyncio.get_running_loop().create_future()
        self._responses[correlation_id] = future

        await self._channel.default_exchange.publish(
            Message(
                body=json.dumps(payload).encode(),
                reply_to=self._callback_queue.name,
                correlation_id=correlation_id,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )

        try:
            body = await asyncio.wait_for(future, timeout)
            return json.loads(body.decode())
        finally:
            self._responses.pop(correlation_id, None)


class TaskRpcConsumer:
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
            RABBITMQ_TASK_QUEUE,
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
            response = await self._build_response(message.body)

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

    async def _get_user_role(self, team_id: UUID, permission: TeamPermission, access_token: str | None) -> dict:
        if not access_token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        payload = await role_rpc_client.call(
            RABBITMQ_ROLE_QUEUE,
            {
                "team_id": str(team_id),
                "action": permission.value,
                "access_token": access_token,
            },
        )

        error = payload.get("error")
        if error:
            raise HTTPException(
                status_code=error.get("status_code", 502),
                detail=error.get("detail", "User service error"),
            )

        if not payload.get("is_allowed"):
            raise HTTPException(status_code=403, detail="insufficient permissions")

        return payload

    async def _build_response(self, body: bytes) -> dict:
        db = SessionLocal()
        try:
            payload = json.loads(body.decode())
            
            action = payload.get("action")
            try:
                permission = TeamPermission(action)
            except ValueError:
                return {
                    "error": {
                        "status_code": 400,
                        "detail": "Unsupported action",
                    }
                }

            team_id = UUID(payload["team_id"])
            current_user = await self._get_user_role(
                team_id=team_id,
                permission=permission,
                access_token=payload.get("access_token"),
            )

            if permission == TeamPermission.CREATE_TASK:
                task = TaskCreate.model_validate(payload["task"])
                result = TaskService.create_task(
                    db=db,
                    task=task,
                    team_id=team_id,
                    created_by=UUID(current_user["user_id"]),
                    idempotency_key=UUID(payload["idempotency_key"]),
                )
            elif permission == TeamPermission.VIEW_USER_TASKS:
                filters = payload.get("filters", {})
                result = TaskService.get_user_tasks(
                    db=db,
                    user_id=UUID(current_user["user_id"]),
                    team_id=team_id,
                    status=filters.get("status"),
                    deadline=filters.get("deadline"),
                    sort=filters.get("sort"),
                    direction=filters.get("direction", "asc"),
                    limit=filters.get("limit", 10),
                    page=filters.get("page", 1),
                )
            elif permission == TeamPermission.VIEW_ALL_TASKS:
                filters = payload.get("filters", {})
                result = TaskService.get_all_team_tasks(
                    db=db,
                    team_id=team_id,
                    status=filters.get("status"),
                    deadline=filters.get("deadline"),
                    sort=filters.get("sort"),
                    direction=filters.get("direction", "asc"),
                    limit=filters.get("limit", 10),
                    page=filters.get("page", 1),
                )
            elif permission == TeamPermission.CHANGE_TASK_STATUS:
                task = TaskChangeStatus.model_validate(payload["task"])
                result = TaskService.change_task_status(
                    db=db,
                    team_id=team_id,
                    user_id=UUID(current_user["user_id"]),
                    task=task,
                    idempotency_key=UUID(payload["idempotency_key"]),
                )
            else:
                task = TaskDelete.model_validate(payload["task"])
                result = TaskService.remove_task(
                    db=db,
                    user_id=UUID(current_user["user_id"]),
                    team_id=team_id,
                    task_id=task.task_id,
                )

            return {"data": self._serialize_result(action, result)}
        except (KeyError, ValidationError):
            return {
                "error": {
                    "status_code": 400,
                    "detail": "Invalid payload",
                }
            }
        except HTTPException as exc:
            return {
                "error": {
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                }
            }
        except TimeoutError:
            return {
                "error": {
                    "status_code": 503,
                    "detail": "User service unavailable",
                }
            }
        except Exception:
            logger.exception("Task RPC consumer failed for action=%s", payload.get("action") if "payload" in locals() else None)
            return {
                "error": {
                    "status_code": 500,
                    "detail": "Task RPC failed",
                }
            }
        finally:
            db.close()

    @staticmethod
    def _serialize_result(action: str, result: object) -> dict:
        if action in {
            TeamPermission.VIEW_USER_TASKS.value,
            TeamPermission.VIEW_ALL_TASKS.value,
        }:
            return PaginatedTaskResponse.model_validate(result).model_dump(mode="json")

        return TaskResponse.model_validate(result).model_dump(mode="json")


role_rpc_client = RoleRpcClient()
task_rpc_consumer = TaskRpcConsumer()
