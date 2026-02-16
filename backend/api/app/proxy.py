from __future__ import annotations
import time
from typing import Dict, Tuple
import httpx
from fastapi import Request, Response, HTTPException
from .config import INAT_BASE_URL, CACHE_TTL_SECONDS

_cache: Dict[str, Tuple[float, bytes, str]] = {}

def _cache_key(request: Request) -> str:
    return f"{request.url.path}?{request.url.query}"

async def forward_get(request: Request, upstream_path: str) -> Response:
    key = _cache_key(request)
    now = time.time()
    if key in _cache:
        expires_at, body, ctype = _cache[key]
        if now < expires_at:
            return Response(content=body, media_type=ctype)

    url = f"{INAT_BASE_URL}/{upstream_path.lstrip('/')}"
    params = dict(request.query_params)

    timeout = httpx.Timeout(20.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(url, params=params, headers={"Accept": "application/json"})
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {e}") from e

    content_type = r.headers.get("content-type", "application/json")
    body = r.content

    if r.status_code == 200 and "application/json" in content_type:
        _cache[key] = (now + CACHE_TTL_SECONDS, body, content_type)

    return Response(content=body, status_code=r.status_code, media_type=content_type)
