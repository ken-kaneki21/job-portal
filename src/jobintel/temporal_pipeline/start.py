import asyncio
from datetime import (
    datetime,
    timezone,
)

from temporalio.client import Client

from jobintel.temporal_pipeline.config import (
    TASK_QUEUE,
    TEMPORAL_ADDRESS,
    TEMPORAL_NAMESPACE,
)
from jobintel.temporal_pipeline.workflow import (
    JobIntelligencePipelineWorkflow,
)


async def start_pipeline() -> str:
    client = await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d-%H%M%S"
    )

    workflow_id = (
        "job-intelligence-pipeline-"
        f"{timestamp}"
    )

    handle = await client.start_workflow(
        JobIntelligencePipelineWorkflow.run,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    return handle.id


async def main() -> None:
    workflow_id = await start_pipeline()

    print()
    print("=" * 80)
    print("TEMPORAL WORKFLOW STARTED")
    print("=" * 80)

    print(
        f"Workflow ID: "
        f"{workflow_id}"
    )

    print(
        "Temporal UI: "
        "http://localhost:8080"
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )