from sqlalchemy import select

from jobintel.db.models import (
    JobApplicationStateRecord,
)

VALID_STATUSES = {
    "new",
    "reviewed",
    "applied",
    "skipped",
    "interview",
    "rejected",
    "offer",
}


def get_application_state(
    session,
    job_id: int,
    profile_name: str,
):
    return session.scalar(
        select(JobApplicationStateRecord).where(
            JobApplicationStateRecord.job_id == job_id,
            JobApplicationStateRecord.profile_name == profile_name,
        )
    )


def set_application_state(
    session,
    job_id: int,
    profile_name: str,
    status: str,
    notes: str | None = None,
):
    status = status.lower().strip()

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status}. Allowed: {', '.join(sorted(VALID_STATUSES))}"
        )

    record = get_application_state(
        session=session,
        job_id=job_id,
        profile_name=profile_name,
    )

    if record is None:
        record = JobApplicationStateRecord(
            job_id=job_id,
            profile_name=profile_name,
            status=status,
            notes=notes,
        )

        session.add(record)

    else:
        record.status = status

        if notes is not None:
            record.notes = notes

    return record
