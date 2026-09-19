from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from jobintel.db.models import JobSourceRecord


def find_source_reference(
    session: Session,
    *,
    source: str,
    source_identifier: str,
    external_id: str,
) -> JobSourceRecord | None:
    return session.scalar(
        select(JobSourceRecord)
        .where(
            JobSourceRecord.source == source,
            JobSourceRecord.source_identifier
            == source_identifier,
            JobSourceRecord.external_id
            == external_id,
        )
    )


def attach_source(
    session: Session,
    *,
    job_id: int,
    source: str,
    source_identifier: str,
    external_id: str,
    source_url: str | None,
    is_primary: bool = False,
) -> None:
    statement = insert(
        JobSourceRecord
    ).values(
        job_id=job_id,
        source=source,
        source_identifier=source_identifier,
        external_id=external_id,
        source_url=source_url,
        is_primary=is_primary,
    )

    statement = statement.on_conflict_do_update(
        constraint="uq_job_source_identity",
        set_={
            "job_id": job_id,
            "source_url": source_url,
            "last_seen_at": func.now(),
        },
    )

    session.execute(statement)