from __future__ import annotations

import logging
import time

from dataclasses import dataclass

from temporalio import activity

from jobintel.pipeline import (
    create_pipeline_run,
    finalize_pipeline_run,
    run_step,
)
from jobintel.temporal_pipeline.observability import (
    record_activity_execution,
    record_pipeline_finalization,
)


LOGGER = logging.getLogger(
    "jobintel.temporal.activities"
)


@dataclass
class PipelineStepInput:
    run_id: int
    label: str
    module: str


@dataclass
class FinalizePipelineInput:
    run_id: int
    success: bool
    error_message: str | None = None


def get_workflow_id() -> str | None:
    try:
        info = activity.info()

        return info.workflow_id

    except Exception:
        return None


@activity.defn
def create_pipeline_run_activity() -> int:
    activity_name = (
        "create_pipeline_run"
    )

    started = (
        time.perf_counter()
    )

    workflow_id = (
        get_workflow_id()
    )

    LOGGER.info(
        "temporal_activity_started",
        extra={
            "service": (
                "jobintel-temporal-worker"
            ),
            "workflow_id": (
                workflow_id
            ),
            "activity_name": (
                activity_name
            ),
        },
    )

    try:
        run_id = (
            create_pipeline_run()
        )

        duration = (
            time.perf_counter()
            - started
        )

        record_activity_execution(
            activity_name=activity_name,
            step_name=None,
            outcome="success",
            duration_seconds=duration,
        )

        LOGGER.info(
            "temporal_activity_completed",
            extra={
                "service": (
                    "jobintel-temporal-worker"
                ),
                "workflow_id": (
                    workflow_id
                ),
                "pipeline_run_id": (
                    run_id
                ),
                "activity_name": (
                    activity_name
                ),
                "duration_seconds": (
                    round(
                        duration,
                        6,
                    )
                ),
            },
        )

        return run_id

    except Exception:
        duration = (
            time.perf_counter()
            - started
        )

        record_activity_execution(
            activity_name=activity_name,
            step_name=None,
            outcome="failure",
            duration_seconds=duration,
        )

        LOGGER.exception(
            "temporal_activity_failed",
            extra={
                "service": (
                    "jobintel-temporal-worker"
                ),
                "workflow_id": (
                    workflow_id
                ),
                "activity_name": (
                    activity_name
                ),
                "duration_seconds": (
                    round(
                        duration,
                        6,
                    )
                ),
            },
        )

        raise


@activity.defn
def run_pipeline_step_activity(
    input_data: PipelineStepInput,
) -> None:
    activity_name = (
        "run_pipeline_step"
    )

    started = (
        time.perf_counter()
    )

    workflow_id = (
        get_workflow_id()
    )

    LOGGER.info(
        "temporal_activity_started",
        extra={
            "service": (
                "jobintel-temporal-worker"
            ),
            "workflow_id": (
                workflow_id
            ),
            "pipeline_run_id": (
                input_data.run_id
            ),
            "activity_name": (
                activity_name
            ),
            "step_name": (
                input_data.label
            ),
        },
    )

    try:
        run_step(
            label=(
                input_data.label
            ),
            module=(
                input_data.module
            ),
            run_id=(
                input_data.run_id
            ),
        )

        duration = (
            time.perf_counter()
            - started
        )

        record_activity_execution(
            activity_name=activity_name,
            step_name=input_data.label,
            outcome="success",
            duration_seconds=duration,
        )

        LOGGER.info(
            "temporal_activity_completed",
            extra={
                "service": (
                    "jobintel-temporal-worker"
                ),
                "workflow_id": (
                    workflow_id
                ),
                "pipeline_run_id": (
                    input_data.run_id
                ),
                "activity_name": (
                    activity_name
                ),
                "step_name": (
                    input_data.label
                ),
                "duration_seconds": (
                    round(
                        duration,
                        6,
                    )
                ),
            },
        )

    except Exception:
        duration = (
            time.perf_counter()
            - started
        )

        record_activity_execution(
            activity_name=activity_name,
            step_name=input_data.label,
            outcome="failure",
            duration_seconds=duration,
        )

        LOGGER.exception(
            "temporal_activity_failed",
            extra={
                "service": (
                    "jobintel-temporal-worker"
                ),
                "workflow_id": (
                    workflow_id
                ),
                "pipeline_run_id": (
                    input_data.run_id
                ),
                "activity_name": (
                    activity_name
                ),
                "step_name": (
                    input_data.label
                ),
                "duration_seconds": (
                    round(
                        duration,
                        6,
                    )
                ),
            },
        )

        raise


@activity.defn
def finalize_pipeline_run_activity(
    input_data: FinalizePipelineInput,
) -> None:
    activity_name = (
        "finalize_pipeline_run"
    )

    started = (
        time.perf_counter()
    )

    workflow_id = (
        get_workflow_id()
    )

    LOGGER.info(
        "temporal_activity_started",
        extra={
            "service": (
                "jobintel-temporal-worker"
            ),
            "workflow_id": (
                workflow_id
            ),
            "pipeline_run_id": (
                input_data.run_id
            ),
            "activity_name": (
                activity_name
            ),
        },
    )

    try:
        finalize_pipeline_run(
            run_id=(
                input_data.run_id
            ),
            success=(
                input_data.success
            ),
            error_message=(
                input_data.error_message
            ),
        )

        duration = (
            time.perf_counter()
            - started
        )

        record_activity_execution(
            activity_name=activity_name,
            step_name=None,
            outcome="success",
            duration_seconds=duration,
        )

        record_pipeline_finalization(
            success=(
                input_data.success
            )
        )

        LOGGER.info(
            "temporal_activity_completed",
            extra={
                "service": (
                    "jobintel-temporal-worker"
                ),
                "workflow_id": (
                    workflow_id
                ),
                "pipeline_run_id": (
                    input_data.run_id
                ),
                "activity_name": (
                    activity_name
                ),
                "duration_seconds": (
                    round(
                        duration,
                        6,
                    )
                ),
            },
        )

    except Exception:
        duration = (
            time.perf_counter()
            - started
        )

        record_activity_execution(
            activity_name=activity_name,
            step_name=None,
            outcome="failure",
            duration_seconds=duration,
        )

        LOGGER.exception(
            "temporal_activity_failed",
            extra={
                "service": (
                    "jobintel-temporal-worker"
                ),
                "workflow_id": (
                    workflow_id
                ),
                "pipeline_run_id": (
                    input_data.run_id
                ),
                "activity_name": (
                    activity_name
                ),
                "duration_seconds": (
                    round(
                        duration,
                        6,
                    )
                ),
            },
        )

        raise