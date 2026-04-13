from fastapi import FastAPI

from app.api.router import api_router


app = FastAPI(
    title="Todo Gateway",
    description="Gateway API that proxies auth, users, teams, and todos endpoints.",
)
app.include_router(api_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
