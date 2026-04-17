import asyncio
import json
import os
from urllib.parse import quote
from uuid import uuid4

import aio_pika
from aio_pika import DeliveryMode, IncomingMessage, Message
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractQueue


RABBITMQ_TASK_QUEUE = os.getenv("RABBITMQ_TASK_QUEUE", "task_queue")

RABBITMQ_URL = (os.getenv("RABBITMQ_URL") or "").strip()
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

class TaskRpcClient:
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
            raise RuntimeError("Task RPC client is not connected")

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


task_rpc_client = TaskRpcClient()
