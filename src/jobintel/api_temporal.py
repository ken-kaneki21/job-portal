from datetime import (
    UTC,
    datetime,
)

from fastapi import (
    APIRouter,
    HTTPException,
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

router = APIRouter(tags=["Temporal"])


def workflow_status_name(status) -> str:
    if status is None:
        return "UNKNOWN"

    return status.name


async def get_temporal_client() -> Client:
    return await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
    )


async def start_temporal_pipeline() -> dict:
    client = await get_temporal_client()

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")

    workflow_id = f"job-intelligence-pipeline-{timestamp}"

    handle = await client.start_workflow(
        JobIntelligencePipelineWorkflow.run,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    return {
        "message": ("Temporal pipeline workflow started"),
        "workflow_id": handle.id,
        "temporal_managed": True,
        "task_queue": TASK_QUEUE,
    }


@router.post("/pipeline/run-temporal")
async def run_pipeline_temporal():
    try:
        return await start_temporal_pipeline()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(f"Unable to start Temporal workflow: {exc}"),
        ) from exc


@router.get("/temporal/workflows/{workflow_id}")
async def get_temporal_workflow_status(
    workflow_id: str,
):
    try:
        client = await get_temporal_client()

        handle = client.get_workflow_handle(workflow_id)

        description = await handle.describe()

        return {
            "workflow_id": workflow_id,
            "status": (workflow_status_name(description.status)),
            "workflow_type": (description.workflow_type),
            "run_id": (description.run_id),
            "task_queue": (description.task_queue),
            "start_time": (
                description.start_time.isoformat() if description.start_time else None
            ),
            "close_time": (
                description.close_time.isoformat() if description.close_time else None
            ),
            "temporal_managed": True,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=(f"Unable to get workflow status: {exc}"),
        ) from exc


@router.get("/temporal/workflows/{workflow_id}/result")
async def get_temporal_workflow_result(
    workflow_id: str,
):
    try:
        client = await get_temporal_client()

        handle = client.get_workflow_handle(workflow_id)

        description = await handle.describe()

        status = workflow_status_name(description.status)

        if status != "COMPLETED":
            return {
                "workflow_id": workflow_id,
                "status": status,
                "result_available": False,
            }

        result = await handle.result()

        return {
            "workflow_id": workflow_id,
            "status": status,
            "result_available": True,
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=(f"Unable to get workflow result: {exc}"),
        ) from exc
