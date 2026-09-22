from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from jobintel.application_ops.status import normalize_status
from jobintel.db.application_event_repository import (
    add_application_event,
    get_application_history,
)
from jobintel.db.models import (
    JobApplicationStateRecord,
    JobRecord,
)


class ApplicationOpsError(RuntimeError):
    pass


def require_job(
    session: Session,
    job_id: int,
) -> JobRecord:
    job = session.get(
        JobRecord,
        job_id,
    )

    if job is None:
        raise ApplicationOpsError(f"Job {job_id} was not found.")

    return job


def get_state(
    *,
    session: Session,
    job_id: int,
    profile_name: str,
) -> JobApplicationStateRecord | None:
    return session.scalar(
        select(JobApplicationStateRecord)
        .where(JobApplicationStateRecord.job_id == job_id)
        .where(JobApplicationStateRecord.profile_name == profile_name)
        .limit(1)
    )


def set_status(
    *,
    session: Session,
    job_id: int,
    profile_name: str,
    status: str,
    notes: str | None = None,
    source: str = "application_ops",
) -> JobApplicationStateRecord:
    require_job(
        session,
        job_id,
    )

    normalized = normalize_status(status)

    record = get_state(
        session=session,
        job_id=job_id,
        profile_name=profile_name,
    )

    if record is None:
        previous_status = "new"

        record = JobApplicationStateRecord(
            job_id=job_id,
            profile_name=profile_name,
            status=normalized,
            notes=notes,
        )

        session.add(record)
    else:
        previous_status = record.status

        record.status = normalized

        if notes is not None:
            record.notes = notes

    if previous_status != normalized:
        add_application_event(
            session=session,
            job_id=job_id,
            profile_name=profile_name,
            previous_status=previous_status,
            new_status=normalized,
            notes=notes,
            source=source,
        )

    session.commit()
    session.refresh(record)

    return record


def history(
    *,
    session: Session,
    job_id: int,
    profile_name: str,
):
    require_job(
        session,
        job_id,
    )

    return get_application_history(
        session=session,
        job_id=job_id,
        profile_name=profile_name,
    )


def status_summary(
    *,
    session: Session,
    profile_name: str,
) -> dict[str, int]:
    rows = session.execute(
        select(
            JobApplicationStateRecord.status,
            func.count(JobApplicationStateRecord.id),
        )
        .where(JobApplicationStateRecord.profile_name == profile_name)
        .group_by(JobApplicationStateRecord.status)
    ).all()

    counts = {str(status): int(count) for status, count in rows}

    for status in (
        "new",
        "seen",
        "saved",
        "dismissed",
        "applied",
        "interviewing",
        "rejected",
        "offer",
    ):
        counts.setdefault(
            status,
            0,
        )

    return counts
