from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleState,
)
from temporalio.service import RPCError, RPCStatusCode

from jobintel.temporal_pipeline.config import (
    DAILY_SCHEDULE_ID,
    TASK_QUEUE,
    TEMPORAL_ADDRESS,
    TEMPORAL_NAMESPACE,
)
from jobintel.temporal_pipeline.schedule_config import (
    DailyScheduleConfig,
    build_schedule_note,
    parse_schedule_note,
)
from jobintel.temporal_pipeline.workflow import JobIntelligencePipelineWorkflow

router = APIRouter(tags=["Temporal"])


class DailyScheduleRequest(BaseModel):
    enabled: bool = True
    hour: int = Field(default=8, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=100)
    send_digest: bool = True


def workflow_status_name(status: Any) -> str:
    if status is None:
        return "UNKNOWN"
    return str(status.name)


async def get_temporal_client() -> Client:
    return await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
    )


async def start_temporal_pipeline() -> dict[str, object]:
    client = await get_temporal_client()
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    workflow_id = f"job-intelligence-pipeline-{timestamp}"

    handle = await client.start_workflow(
        JobIntelligencePipelineWorkflow.run,
        False,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    return {
        "message": "Temporal pipeline workflow started",
        "workflow_id": handle.id,
        "temporal_managed": True,
        "task_queue": TASK_QUEUE,
    }


def is_not_found(exc: RPCError) -> bool:
    return exc.status == RPCStatusCode.NOT_FOUND


async def get_daily_schedule_description(client: Client):
    handle = client.get_schedule_handle(DAILY_SCHEDULE_ID)
    try:
        return await handle.describe()
    except RPCError as exc:
        if is_not_found(exc):
            return None
        raise


def serialize_schedule_description(description: Any) -> dict[str, object]:
    schedule = description.schedule
    state = schedule.state
    info = description.info
    config = parse_schedule_note(state.note)

    next_action_times = [value.isoformat() for value in info.next_action_times]

    return {
        "exists": True,
        "schedule_id": DAILY_SCHEDULE_ID,
        "enabled": not state.paused,
        "hour": config.hour,
        "minute": config.minute,
        "timezone": config.timezone,
        "send_digest": config.send_digest,
        "next_run_at": next_action_times[0] if next_action_times else None,
        "next_action_times": next_action_times,
        "num_actions": info.num_actions,
        "num_actions_missed_catchup_window": info.num_actions_missed_catchup_window,
        "num_actions_skipped_overlap": info.num_actions_skipped_overlap,
        "running_actions": len(info.running_actions),
        "task_queue": TASK_QUEUE,
        "overlap_policy": "skip",
    }


def schedule_absent_response() -> dict[str, object]:
    default = DailyScheduleConfig()
    return {
        "exists": False,
        "schedule_id": DAILY_SCHEDULE_ID,
        "enabled": False,
        "hour": default.hour,
        "minute": default.minute,
        "timezone": default.timezone,
        "send_digest": default.send_digest,
        "next_run_at": None,
        "next_action_times": [],
        "num_actions": 0,
        "num_actions_missed_catchup_window": 0,
        "num_actions_skipped_overlap": 0,
        "running_actions": 0,
        "task_queue": TASK_QUEUE,
        "overlap_policy": "skip",
    }


def build_daily_schedule(request: DailyScheduleRequest) -> Schedule:
    try:
        config = DailyScheduleConfig(
            hour=request.hour,
            minute=request.minute,
            timezone=request.timezone,
            send_digest=request.send_digest,
        ).validate()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workflow_id = f"{DAILY_SCHEDULE_ID}-workflow"

    return Schedule(
        action=ScheduleActionStartWorkflow(
            JobIntelligencePipelineWorkflow.run,
            config.send_digest,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        ),
        spec=ScheduleSpec(
            cron_expressions=[f"{config.minute} {config.hour} * * *"],
            time_zone_name=config.timezone,
        ),
        policy=SchedulePolicy(
            overlap=ScheduleOverlapPolicy.SKIP,
            pause_on_failure=False,
        ),
        state=ScheduleState(
            paused=not request.enabled,
            note=build_schedule_note(config),
        ),
    )


@router.post("/pipeline/run-temporal")
async def run_pipeline_temporal():
    try:
        return await start_temporal_pipeline()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to start Temporal workflow: {exc}",
        ) from exc


@router.get("/temporal/workflows/{workflow_id}")
async def get_temporal_workflow_status(workflow_id: str):
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        description = await handle.describe()
        status = workflow_status_name(description.status)
        progress = None

        if status == "RUNNING":
            try:
                progress = await handle.query(JobIntelligencePipelineWorkflow.progress)
            except Exception:
                progress = None

        return {
            "workflow_id": workflow_id,
            "status": status,
            "workflow_type": description.workflow_type,
            "run_id": description.run_id,
            "task_queue": description.task_queue,
            "start_time": (
                description.start_time.isoformat() if description.start_time else None
            ),
            "close_time": (
                description.close_time.isoformat() if description.close_time else None
            ),
            "temporal_managed": True,
            "progress": progress,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to get workflow status: {exc}",
        ) from exc


@router.get("/temporal/workflows/{workflow_id}/result")
async def get_temporal_workflow_result(workflow_id: str):
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
            detail=f"Unable to get workflow result: {exc}",
        ) from exc


@router.get("/temporal/schedules/daily")
async def get_daily_schedule():
    try:
        client = await get_temporal_client()
        description = await get_daily_schedule_description(client)
        if description is None:
            return schedule_absent_response()
        return serialize_schedule_description(description)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to read daily schedule: {exc}",
        ) from exc


@router.put("/temporal/schedules/daily")
async def put_daily_schedule(request: DailyScheduleRequest):
    try:
        client = await get_temporal_client()
        schedule = build_daily_schedule(request)
        existing = await get_daily_schedule_description(client)

        if existing is not None:
            await client.get_schedule_handle(DAILY_SCHEDULE_ID).delete()

        await client.create_schedule(
            DAILY_SCHEDULE_ID,
            schedule,
        )

        description = await get_daily_schedule_description(client)
        if description is None:
            raise RuntimeError("Schedule was created but could not be described.")

        return serialize_schedule_description(description)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save daily schedule: {exc}",
        ) from exc


@router.post("/temporal/schedules/daily/pause")
async def pause_daily_schedule():
    try:
        client = await get_temporal_client()
        description = await get_daily_schedule_description(client)
        if description is None:
            raise HTTPException(status_code=404, detail="Daily schedule not found.")

        note = description.schedule.state.note
        handle = client.get_schedule_handle(DAILY_SCHEDULE_ID)
        await handle.pause(note=note)
        return serialize_schedule_description(await handle.describe())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to pause daily schedule: {exc}",
        ) from exc


@router.post("/temporal/schedules/daily/resume")
async def resume_daily_schedule():
    try:
        client = await get_temporal_client()
        description = await get_daily_schedule_description(client)
        if description is None:
            raise HTTPException(status_code=404, detail="Daily schedule not found.")

        note = description.schedule.state.note
        handle = client.get_schedule_handle(DAILY_SCHEDULE_ID)
        await handle.unpause(note=note)
        return serialize_schedule_description(await handle.describe())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to resume daily schedule: {exc}",
        ) from exc


@router.post("/temporal/schedules/daily/trigger")
async def trigger_daily_schedule():
    try:
        client = await get_temporal_client()
        description = await get_daily_schedule_description(client)
        if description is None:
            raise HTTPException(status_code=404, detail="Daily schedule not found.")

        handle = client.get_schedule_handle(DAILY_SCHEDULE_ID)
        await handle.trigger(overlap=ScheduleOverlapPolicy.SKIP)
        return {
            "message": "Daily schedule triggered.",
            "schedule_id": DAILY_SCHEDULE_ID,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to trigger daily schedule: {exc}",
        ) from exc
