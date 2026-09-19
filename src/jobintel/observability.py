from __future__ import annotations

import json
import logging
import sys
import time
import uuid

from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)


request_id_context: ContextVar[
    str | None
] = ContextVar(
    "request_id",
    default=None,
)


API_REQUESTS_TOTAL = Counter(
    "jobintel_api_requests_total",
    (
        "Total number of Job Intelligence "
        "API requests"
    ),
    [
        "method",
        "path",
        "status",
    ],
)


API_REQUEST_DURATION_SECONDS = Histogram(
    "jobintel_api_request_duration_seconds",
    (
        "Duration of Job Intelligence "
        "API requests in seconds"
    ),
    [
        "method",
        "path",
    ],
)


class JsonFormatter(
    logging.Formatter
):
    """
    Convert Python log records into one-line
    JSON objects.

    Extra structured fields can be attached
    through logging's `extra={...}` argument.
    """

    STRUCTURED_FIELDS = (
        "service",
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_seconds",
        "workflow_id",
        "pipeline_run_id",
        "activity_name",
        "step_name",
        "job_id",
    )

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        payload: dict[
            str,
            Any,
        ] = {
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "level": (
                record.levelname
            ),
            "logger": (
                record.name
            ),
            "message": (
                record.getMessage()
            ),
        }

        context_request_id = (
            request_id_context.get()
        )

        if context_request_id:
            payload[
                "request_id"
            ] = context_request_id

        for field in (
            self.STRUCTURED_FIELDS
        ):
            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:
                payload[
                    field
                ] = value

        if record.exc_info:
            payload[
                "exception"
            ] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            payload,
            default=str,
            ensure_ascii=False,
        )


def configure_logging(
    service_name: str,
    *,
    level: int = logging.INFO,
) -> None:
    """
    Configure application logging once using
    JSON output.

    This intentionally configures the root
    logger so all jobintel modules inherit the
    same output format.
    """

    root_logger = (
        logging.getLogger()
    )

    root_logger.setLevel(
        level
    )

    handler = (
        logging.StreamHandler(
            sys.stdout
        )
    )

    handler.setFormatter(
        JsonFormatter()
    )

    root_logger.handlers.clear()

    root_logger.addHandler(
        handler
    )

    # Uvicorn's normal access logger would
    # otherwise duplicate our API request log.
    logging.getLogger(
        "uvicorn.access"
    ).propagate = False

    logging.getLogger(
        "jobintel"
    ).info(
        "logging_configured",
        extra={
            "service": (
                service_name
            ),
        },
    )


def get_request_id() -> str | None:
    return request_id_context.get()


def _resolve_metric_path(
    request: Request,
) -> str:
    """
    Prefer the FastAPI route template instead
    of the literal URL.

    Example:

        /jobs/123
        /jobs/456

    are recorded as:

        /jobs/{job_id}

    This prevents Prometheus label cardinality
    from exploding.
    """

    route = request.scope.get(
        "route"
    )

    route_path = getattr(
        route,
        "path",
        None,
    )

    if route_path:
        return str(
            route_path
        )

    return request.url.path


class CorrelationIdMiddleware(
    BaseHTTPMiddleware
):
    """
    Adds X-Request-ID to every HTTP request.

    If the caller already supplies an
    X-Request-ID header, it is preserved.

    The middleware also records:
      - request count
      - HTTP status
      - route template
      - request duration
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        request_id = (
            request.headers.get(
                "X-Request-ID"
            )
            or str(
                uuid.uuid4()
            )
        )

        token = (
            request_id_context.set(
                request_id
            )
        )

        started = (
            time.perf_counter()
        )

        method = (
            request.method
        )

        logger = logging.getLogger(
            "jobintel.api"
        )

        status_code = 500

        try:
            response = await call_next(
                request
            )

            status_code = (
                response.status_code
            )

            response.headers[
                "X-Request-ID"
            ] = request_id

            return response

        except Exception:
            logger.exception(
                "api_request_failed",
                extra={
                    "service": (
                        "jobintel-api"
                    ),
                    "method": (
                        method
                    ),
                    "path": (
                        request.url.path
                    ),
                    "status_code": (
                        status_code
                    ),
                },
            )

            raise

        finally:
            duration = (
                time.perf_counter()
                - started
            )

            metric_path = (
                _resolve_metric_path(
                    request
                )
            )

            API_REQUESTS_TOTAL.labels(
                method=method,
                path=metric_path,
                status=str(
                    status_code
                ),
            ).inc()

            API_REQUEST_DURATION_SECONDS.labels(
                method=method,
                path=metric_path,
            ).observe(
                duration
            )

            logger.info(
                "api_request_completed",
                extra={
                    "service": (
                        "jobintel-api"
                    ),
                    "method": (
                        method
                    ),
                    "path": (
                        metric_path
                    ),
                    "status_code": (
                        status_code
                    ),
                    "duration_seconds": (
                        round(
                            duration,
                            6,
                        )
                    ),
                },
            )

            request_id_context.reset(
                token
            )


def metrics_response() -> Response:
    """
    Render the current Prometheus registry.
    """

    return Response(
        content=generate_latest(),
        media_type=(
            CONTENT_TYPE_LATEST
        ),
    )