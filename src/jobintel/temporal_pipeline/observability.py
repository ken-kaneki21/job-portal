from __future__ import annotations

import logging

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)


LOGGER = logging.getLogger(
    "jobintel.temporal.metrics"
)


TEMPORAL_ACTIVITY_EXECUTIONS_TOTAL = Counter(
    "jobintel_temporal_activity_executions_total",
    (
        "Total number of Job Intelligence "
        "Temporal activity executions"
    ),
    [
        "activity_name",
        "step_name",
        "outcome",
    ],
)


TEMPORAL_ACTIVITY_DURATION_SECONDS = Histogram(
    "jobintel_temporal_activity_duration_seconds",
    (
        "Duration of Job Intelligence "
        "Temporal activities in seconds"
    ),
    [
        "activity_name",
        "step_name",
    ],
)


PIPELINE_FINALIZATIONS_TOTAL = Counter(
    "jobintel_pipeline_finalizations_total",
    (
        "Total number of Job Intelligence "
        "pipeline finalizations"
    ),
    [
        "success",
    ],
)


TEMPORAL_WORKER_UP = Gauge(
    "jobintel_temporal_worker_up",
    (
        "Whether the Job Intelligence "
        "Temporal worker process is running"
    ),
)


def normalize_step_name(
    step_name: str | None,
) -> str:
    if not step_name:
        return "__none__"

    return step_name


def record_activity_execution(
    *,
    activity_name: str,
    step_name: str | None,
    outcome: str,
    duration_seconds: float,
) -> None:
    normalized_step = (
        normalize_step_name(
            step_name
        )
    )

    TEMPORAL_ACTIVITY_EXECUTIONS_TOTAL.labels(
        activity_name=activity_name,
        step_name=normalized_step,
        outcome=outcome,
    ).inc()

    TEMPORAL_ACTIVITY_DURATION_SECONDS.labels(
        activity_name=activity_name,
        step_name=normalized_step,
    ).observe(
        duration_seconds
    )


def record_pipeline_finalization(
    *,
    success: bool,
) -> None:
    PIPELINE_FINALIZATIONS_TOTAL.labels(
        success=(
            "true"
            if success
            else "false"
        )
    ).inc()


def start_worker_metrics_server(
    *,
    port: int = 9101,
) -> None:
    """
    Start a Prometheus HTTP metrics server
    for the Temporal worker.

    It binds to 0.0.0.0 so a Prometheus
    container on Docker Desktop can reach the
    host worker using host.docker.internal.

    This is intended for local/private
    development. Production deployment can
    restrict networking separately.
    """

    start_http_server(
        port,
        addr="0.0.0.0",
    )

    TEMPORAL_WORKER_UP.set(
        1
    )

    LOGGER.info(
        "temporal_worker_metrics_server_started",
        extra={
            "service": (
                "jobintel-temporal-worker"
            ),
        },
    )