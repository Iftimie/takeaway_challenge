import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("takeaway.requests")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        started = perf_counter()
        error_type = None
        try:
            response = await call_next(request)
        except Exception as error:
            # Exception messages/tracebacks can contain SQL values or credentials.
            error_type = type(error).__name__
            response = JSONResponse({"detail": "Internal server error"}, status_code=500)

        response.headers["X-Request-ID"] = request_id
        route = request.scope.get("route")
        method = request.method if request.method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
        record = {
            "request_id": request_id,
            "method": method,
            # Templates omit user-supplied path values; unmatched URLs are omitted.
            "route": getattr(route, "path", "<unmatched>"),
            "status": response.status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        }
        if error_type:
            record["error_type"] = error_type
        record.update(getattr(request.state, "log_payloads", {}))
        level = logging.ERROR if response.status_code >= 500 else logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(level, json.dumps(record, ensure_ascii=False))
        return response
