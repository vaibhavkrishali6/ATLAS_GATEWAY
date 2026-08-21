"""Request ID context, propagation, and request completion logging."""

from time import perf_counter
from uuid import uuid4

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from atlas.logging.logger import log_gateway_request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Preserve or generate request IDs for every HTTP request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            self._log(request, status_code=500, started_at=started_at, level=logging.ERROR)
            raise

        response.headers["X-Request-ID"] = request_id
        level = logging.INFO if response.status_code < 400 else logging.WARNING
        self._log(request, response.status_code, started_at, level)
        return response

    @staticmethod
    def _log(
        request: Request, status_code: int, started_at: float, level: int) -> None:
        if status_code == 401:
            event = "authentication_failed"
        elif status_code == 403:
            event = "authorization_failed"
        elif status_code == 502:
            event = "downstream_request_failed"
        elif status_code >= 500:
            event = "gateway_error"
        else:
            event = "request_completed"

        path_parts = request.url.path.split("/")
        service = path_parts[2] if len(path_parts) > 2 and path_parts[1] == "api" else None
        log_gateway_request(
            event=event,
            level=level,
            request_id=request.state.request_id,
            method=request.method,
            path=request.url.path,
            service=service,
            status_code=status_code,
            duration_ms=round((perf_counter() - started_at) * 1000),
        )
