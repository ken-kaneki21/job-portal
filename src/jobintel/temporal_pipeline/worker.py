from __future__ import annotations

import asyncio
import logging

from concurrent.futures import (
    ThreadPoolExecutor,
)

from temporalio.client import Client
from temporalio.worker import Worker

from jobintel.observability import (
    configure_logging,
)
from jobintel.temporal_pipeline.activities import (
    create_pipeline_run_activity,
    finalize_pipeline_run_activity,
    run_pipeline_step_activity,
)
from jobintel.temporal_pipeline.config import (
    TASK_QUEUE,
    TEMPORAL_ADDRESS,
    TEMPORAL_NAMESPACE,
)
from jobintel.temporal_pipeline.observability import (
    start_worker_metrics_server,
)
from jobintel.temporal_pipeline.workflow import (
    JobIntelligencePipelineWorkflow,
)


LOGGER = logging.getLogger(
    "jobintel.temporal.worker"
)


async def main() -> None:
    configure_logging(
        "jobintel-temporal-worker"
    )

    start_worker_metrics_server(
        port=9101
    )

    LOGGER.info(
        "temporal_worker_connecting",
        extra={
            "service": (
                "jobintel-temporal-worker"
            ),
        },
    )

    client = await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=(
            TEMPORAL_NAMESPACE
        ),
    )

    LOGGER.info(
        "temporal_worker_connected",
        extra={
            "service": (
                "jobintel-temporal-worker"
            ),
        },
    )

    activity_executor = (
        ThreadPoolExecutor(
            max_workers=8
        )
    )

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            JobIntelligencePipelineWorkflow,
        ],
        activities=[
            create_pipeline_run_activity,
            run_pipeline_step_activity,
            finalize_pipeline_run_activity,
        ],
        activity_executor=(
            activity_executor
        ),
    )

    LOGGER.info(
        "temporal_worker_started",
        extra={
            "service": (
                "jobintel-temporal-worker"
            ),
        },
    )

    try:
        await worker.run()

    finally:
        activity_executor.shutdown(
            wait=True
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )