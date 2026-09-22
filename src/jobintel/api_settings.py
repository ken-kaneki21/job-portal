from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


def configured(
    name: str,
) -> bool:
    return bool(
        os.getenv(
            name,
            "",
        ).strip()
    )


def env_flag(
    name: str,
    default: bool = False,
) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@router.get("/status")
def settings_status():
    return {
        "ai": {
            "openai": configured("OPENAI_API_KEY"),
            "groq": configured("GROQ_API_KEY"),
        },
        "integrations": {
            "adzuna": (configured("ADZUNA_APP_ID") and configured("ADZUNA_APP_KEY")),
            "resend": (
                configured("RESEND_API_KEY")
                and configured("NOTIFICATION_FROM_EMAIL")
                and configured("NOTIFICATION_TO_EMAIL")
            ),
            "temporal": True,
        },
        "preferences": {
            "job_max_age_days": int(
                os.getenv(
                    "JOBINTEL_JOB_MAX_AGE_DAYS",
                    "30",
                )
            ),
            "daily_digest_enabled": env_flag(
                "JOBINTEL_DAILY_DIGEST_ENABLED",
                default=False,
            ),
            "daily_digest_max_jobs": int(
                os.getenv(
                    "JOBINTEL_DAILY_DIGEST_MAX_JOBS",
                    "10",
                )
            ),
        },
        "privacy": {
            "review_before_submit": True,
            "auto_submit_enabled": False,
        },
    }
