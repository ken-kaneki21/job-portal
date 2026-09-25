from __future__ import annotations

import os

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
)

from jobintel.temporal_pipeline.config import TASK_QUEUE


def enabled() -> bool:
    return os.getenv("JOBINTEL_AUTO_SCHEDULE_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def schedule_id() -> str:
    return os.getenv("JOBINTEL_TEMPORAL_SCHEDULE_ID", "job-intelligence-daily")


async def ensure_daily_schedule(client: Client) -> dict[str, str | bool]:
    if not enabled():
        return {"enabled": False, "created": False, "schedule_id": schedule_id()}
    cron = os.getenv("JOBINTEL_DAILY_CRON", "0 8 * * *")
    timezone = os.getenv("JOBINTEL_DAILY_TIMEZONE", "Asia/Kolkata")
    try:
        await client.create_schedule(
            schedule_id(),
            Schedule(
                action=ScheduleActionStartWorkflow(
                    "JobIntelligencePipelineWorkflow",
                    id="job-intelligence-daily-workflow",
                    task_queue=TASK_QUEUE,
                ),
                spec=ScheduleSpec(
                    cron_expressions=[cron],
                    time_zone_name=timezone,
                ),
            ),
        )
        created = True
    except Exception as exc:
        if "already" not in str(exc).lower() and "exist" not in str(exc).lower():
            raise
        created = False
    return {
        "enabled": True,
        "created": created,
        "schedule_id": schedule_id(),
        "cron": cron,
        "timezone": timezone,
    }
