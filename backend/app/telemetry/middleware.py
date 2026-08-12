import time
from uuid import uuid4
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.session import engine


class RequestTelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration = round((time.perf_counter() - started) * 1000)
        try:
            with engine.begin() as db:
                db.execute(text("INSERT INTO telemetry.api_requests (endpoint,method,status_code,duration_ms,user_role) VALUES (:p,:m,:s,:d,:r)"), {
                    "p": request.url.path, "m": request.method, "s": response.status_code,
                    "d": duration, "r": request.headers.get("x-user-role")})
        except Exception:
            pass
        return response
