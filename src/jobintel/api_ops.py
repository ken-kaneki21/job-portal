from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException
from temporalio.client import Client

from jobintel.notifications.resend_provider import send_email
from jobintel.temporal_pipeline.config import TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE
from jobintel.temporal_pipeline.schedule import ensure_daily_schedule, schedule_id

router = APIRouter(prefix="/ops", tags=["Operations"])


async def temporal_client() -> Client:
    return await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)


@router.get("/status")
async def status():
    return {
        "schedule": {
            "enabled": os.getenv("JOBINTEL_AUTO_SCHEDULE_ENABLED", "false").lower()
            in {"1", "true", "yes", "on"},
            "id": schedule_id(),
            "cron": os.getenv("JOBINTEL_DAILY_CRON", "0 8 * * *"),
            "timezone": os.getenv("JOBINTEL_DAILY_TIMEZONE", "Asia/Kolkata"),
        },
        "notifications": {
            "daily_digest_enabled": os.getenv(
                "JOBINTEL_DAILY_DIGEST_ENABLED", "false"
            ).lower()
            in {"1", "true", "yes", "on"},
            "resend_configured": bool(
                os.getenv("RESEND_API_KEY")
                and os.getenv("NOTIFICATION_FROM_EMAIL")
                and os.getenv("NOTIFICATION_TO_EMAIL")
            ),
        },
        "security": {
            "auth_configured": bool(
                os.getenv("JOBINTEL_AUTH_USERNAME")
                and os.getenv("JOBINTEL_AUTH_PASSWORD")
                and os.getenv("JOBINTEL_SESSION_SECRET")
            ),
            "companion_token_configured": bool(os.getenv("JOBINTEL_COMPANION_TOKEN")),
        },
        "performance": {
            "embedding_batch_size": int(
                os.getenv("JOBINTEL_EMBEDDING_BATCH_SIZE", "32")
            )
        },
    }


@router.post("/schedule/ensure")
async def ensure_schedule():
    try:
        return await ensure_daily_schedule(await temporal_client())
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Unable to ensure schedule: {exc}"
        ) from exc


@router.post("/schedule/trigger")
async def trigger_schedule():
    try:
        handle = (await temporal_client()).get_schedule_handle(schedule_id())
        await handle.trigger()
        return {"triggered": True, "schedule_id": schedule_id()}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Unable to trigger schedule: {exc}"
        ) from exc


@router.post("/notifications/test")
def test_notification():
    try:
        email_id = send_email(
            subject="Job Intelligence production notification test",
            html="<h2>Job Intelligence</h2><p>Production email delivery is configured correctly.</p>",
            idempotency_key=f"jobintel/test/{uuid.uuid4()}",
        )
        return {"sent": True, "email_id": email_id}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Unable to send test email: {exc}"
        ) from exc


@router.post("/workflows/{workflow_id}/terminate")
async def terminate_workflow(workflow_id: str):
    try:
        handle = (await temporal_client()).get_workflow_handle(workflow_id)
        await handle.terminate(
            "Operator cleanup from Job Intelligence production console"
        )
        return {"terminated": True, "workflow_id": workflow_id}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Unable to terminate workflow: {exc}"
        ) from exc
