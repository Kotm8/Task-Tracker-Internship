from fastapi import HTTPException, Request
from fastapi.responses import Response
import httpx
from app.core.config import USER_API_BASE, TODO_API_BASE

async def proxy_request(request: Request, target_url: str) -> Response:
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }

    async with httpx.AsyncClient() as client:
        try:
            upstream_response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                params=request.query_params,
                headers=headers,
                cookies=request.cookies,
                timeout=10.0,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Upstream service unavailable: {exc.request.url.host}",
            )

    response_headers = {}
    content_type = upstream_response.headers.get("content-type")
    if content_type:
        response_headers["content-type"] = content_type

    response = Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )

    for cookie in upstream_response.headers.get_list("set-cookie"):
        response.headers.append("set-cookie", cookie)

    return response
