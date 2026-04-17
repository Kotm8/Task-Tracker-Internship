from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import router
from app.core.rabbitmq import role_rpc_consumer
from app.core.redis_client import redis_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_manager.init()
    await role_rpc_consumer.start()

    try:
        yield
    finally:
        await role_rpc_consumer.stop()
        redis_manager.close()

app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
