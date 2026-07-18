from __future__ import annotations

import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.metrics import get_metrics_provider

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that collects request and error metrics."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        metrics = get_metrics_provider()
        method = request.method
        path = request.url.path
        labels = {"method": method, "path": path}

        metrics.increment_counter("requests_total", labels=labels)
        metrics.set_gauge("active_requests", 1.0, labels=labels)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            metrics.increment_counter("errors_total", labels=labels)
            raise
        finally:
            elapsed = time.perf_counter() - start_time
            metrics.observe_histogram("request_duration_seconds", elapsed, labels=labels)
            metrics.set_gauge("active_requests", 0.0, labels=labels)
