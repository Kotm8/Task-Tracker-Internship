from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.rabbitmq import task_rpc_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await task_rpc_client.connect()
    try:
        yield
    finally:
        await task_rpc_client.close()

app = FastAPI(
    title="Todo Gateway",
    description="Gateway API that proxies auth, users, teams, and todos endpoints.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
