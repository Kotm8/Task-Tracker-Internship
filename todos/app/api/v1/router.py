from fastapi import APIRouter
from app.api.v1.endpoints import tasks, audit

router = APIRouter()

router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])