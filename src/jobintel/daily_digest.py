from __future__ import annotations

import os
from datetime import (
    UTC,
    datetime,
    timedelta,
)

from sqlalchemy import (
    func,
    select,
)

from jobintel.db.models import (
    JobRankingRecord,
    JobRecord,
)
from jobintel.db.session import SessionLocal
from jobintel.notifications.resend_provider import (
    send_email,
)
from jobintel.notifications.templates import (
    build_daily_digest_email,
)
from jobintel.profile.runtime import (
    ACTIVE_PROFILE_NAME,
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


def main() -> None:
    if not env_flag(
        "JOBINTEL_DAILY_DIGEST_ENABLED",
        default=False,
    ):
        print("Daily email digest disabled.")
        return

    run_value = os.getenv("JOBINTEL_PIPELINE_RUN_ID")

    if not run_value:
        raise RuntimeError("JOBINTEL_PIPELINE_RUN_ID is required.")

    pipeline_run_id = int(run_value)

    max_jobs = max(
        1,
        int(
            os.getenv(
                "JOBINTEL_DAILY_DIGEST_MAX_JOBS",
                "10",
            )
        ),
    )

    max_age_days = max(
        1,
        int(
            os.getenv(
                "JOBINTEL_JOB_MAX_AGE_DAYS",
                "30",
            )
        ),
    )

    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)

    effective_date = func.coalesce(
        JobRecord.posted_at,
        JobRecord.first_seen_at,
    )

    with SessionLocal() as session:
        rows = session.execute(
            select(
                JobRecord,
                JobRankingRecord,
            )
            .join(
                JobRankingRecord,
                JobRankingRecord.job_id == JobRecord.id,
            )
            .where(JobRankingRecord.profile_name == ACTIVE_PROFILE_NAME)
            .where(JobRankingRecord.pipeline_run_id == pipeline_run_id)
            .where(
                JobRankingRecord.bucket.in_(
                    [
                        "high_confidence",
                        "discovery",
                    ]
                )
            )
            .where(JobRecord.is_active.is_(True))
            .where(effective_date >= cutoff)
            .order_by(
                JobRankingRecord.score.desc(),
                effective_date.desc(),
            )
            .limit(max_jobs)
        ).all()

    if not rows:
        print("Daily email digest skipped: " "no fresh ranked jobs.")
        return

    jobs = [
        {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "apply_url": job.apply_url,
            "score": ranking.score,
            "bucket": ranking.bucket,
        }
        for job, ranking in rows
    ]

    subject, html = build_daily_digest_email(
        jobs=jobs,
        pipeline_run_id=pipeline_run_id,
    )

    email_id = send_email(
        subject=subject,
        html=html,
        idempotency_key=(f"jobintel/daily-digest/{pipeline_run_id}"),
    )

    print("Daily digest sent: " f"{email_id} ({len(jobs)} jobs)")


if __name__ == "__main__":
    main()
