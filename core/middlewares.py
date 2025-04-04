from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.redis_client import RedisPool


class RequestCountMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_pool: RedisPool):
        super().__init__(app)
        self.redis_pool = redis_pool

    async def dispatch(self, request: Request, call_next):
        async with self.redis_pool.get_redis() as redis:
            await redis.incr('request_count')
        response = await call_next(request)
        return response


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.endswith("/") or "." in request.url.path.split("/")[-1]:
            return await call_next(request)
        return RedirectResponse(url=f"{request.url.path}/")