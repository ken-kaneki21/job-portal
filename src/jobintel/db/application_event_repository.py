from sqlalchemy import select

from jobintel.db.application_event_model import (
    JobApplicationEventRecord,
)


def add_application_event(
    *,
    session,
    job_id: int,
    profile_name: str,
    previous_status: str | None,
    new_status: str,
    notes: str | None = None,
    source: str = "api",
) -> JobApplicationEventRecord:
    record = JobApplicationEventRecord(
        job_id=job_id,
        profile_name=profile_name,
        previous_status=previous_status,
        new_status=new_status,
        notes=notes,
        source=source,
    )

    session.add(record)

    return record


def get_application_history(
    *,
    session,
    job_id: int,
    profile_name: str,
) -> list[JobApplicationEventRecord]:
    return session.scalars(
        select(JobApplicationEventRecord)
        .where(JobApplicationEventRecord.job_id == job_id)
        .where(JobApplicationEventRecord.profile_name == profile_name)
        .order_by(
            JobApplicationEventRecord.created_at.asc(),
            JobApplicationEventRecord.id.asc(),
        )
    ).all()
