from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router
from app.core.rabbitmq import role_rpc_client, task_rpc_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await role_rpc_client.connect()
    await task_rpc_consumer.start()
    try:
        yield
    finally:
        await task_rpc_consumer.stop()
        await role_rpc_client.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
