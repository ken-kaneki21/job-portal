from dataclasses import dataclass

from sqlalchemy.orm import Session

from jobintel.db.models import (
    JobRecord,
    RawJobRecord,
)
from jobintel.db.provenance import (
    attach_source,
    find_source_reference,
)
from jobintel.dedup import canonical_key
from jobintel.matching import (
    find_cross_source_match,
)
from jobintel.models.fetched_job import FetchedJob


@dataclass(frozen=True)
class BroadSyncResult:
    new: int = 0
    matched_existing: int = 0
    existing_source: int = 0
    raw_saved: int = 0


def persist_broad_jobs(
    session: Session,
    fetched_jobs: list[FetchedJob],
) -> BroadSyncResult:
    new_count = 0
    matched_count = 0
    existing_source_count = 0
    raw_count = 0

    for fetched in fetched_jobs:
        job = fetched.job

        existing_reference = find_source_reference(
            session=session,
            source=job.source,
            source_identifier=job.source_identifier,
            external_id=job.external_id,
        )

        if existing_reference is not None:
            existing_source_count += 1
            continue

        match = find_cross_source_match(
            session=session,
            job=job,
        )

        if match.matched and match.job_id is not None:
            attach_source(
                session=session,
                job_id=match.job_id,
                source=job.source,
                source_identifier=job.source_identifier,
                external_id=job.external_id,
                source_url=str(job.apply_url),
                is_primary=False,
            )

            matched_count += 1

        else:
            record = JobRecord(
                source=job.source,
                source_identifier=job.source_identifier,
                external_id=job.external_id,
                company=job.company,
                title=job.title,
                location=job.location,
                department=job.department,
                description=job.description,
                apply_url=str(job.apply_url),
                posted_at=job.posted_at,
                source_updated_at=job.updated_at,
                fingerprint=job.fingerprint,
                canonical_key=canonical_key(
                    company=job.company,
                    title=job.title,
                    location=job.location,
                ),
                is_active=True,
            )

            session.add(record)
            session.flush()

            attach_source(
                session=session,
                job_id=record.id,
                source=job.source,
                source_identifier=job.source_identifier,
                external_id=job.external_id,
                source_url=str(job.apply_url),
                is_primary=True,
            )

            new_count += 1

        session.add(
            RawJobRecord(
                source=job.source,
                source_identifier=job.source_identifier,
                external_id=job.external_id,
                payload=fetched.raw,
            )
        )

        raw_count += 1

    return BroadSyncResult(
        new=new_count,
        matched_existing=matched_count,
        existing_source=existing_source_count,
        raw_saved=raw_count,
    )
