from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import router
from app.core.redis_client import redis_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_manager.init()
    yield
    redis_manager.close()

app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/api/v1")
