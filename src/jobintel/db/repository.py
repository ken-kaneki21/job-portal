from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, TypeVar

from sqlalchemy import (
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import (
    insert,
)
from sqlalchemy.orm import Session

from jobintel.db.models import (
    JobRecord,
    RawJobRecord,
    ScanRecord,
)
from jobintel.dedup import (
    canonical_key,
)
from jobintel.models.job import (
    Job,
)


# Keep multi-row PostgreSQL statements comfortably
# below driver / PostgreSQL bind-parameter limits.
#
# A JobRecord upsert currently contains roughly
# 15 bound values per row.
#
# 500 rows therefore produces only several
# thousand parameters instead of tens of
# thousands in one statement.
UPSERT_BATCH_SIZE = 500

# Large IN (...) lists are also processed in
# bounded chunks where doing so is semantically
# safe.
ID_BATCH_SIZE = 1000


T = TypeVar("T")


@dataclass(frozen=True)
class SyncResult:
    new: int = 0
    updated: int = 0
    unchanged: int = 0
    reopened: int = 0
    closed: int = 0

    changed_external_ids: (
        frozenset[str]
    ) = frozenset()


def chunked(
    values: list[T],
    batch_size: int,
) -> Iterator[list[T]]:
    """
    Yield bounded slices from a list.

    No commits happen here. The caller retains
    control of the surrounding SQLAlchemy
    transaction, so company synchronization
    remains atomic.
    """

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be greater than 0"
        )

    for start in range(
        0,
        len(values),
        batch_size,
    ):
        yield values[
            start:
            start + batch_size
        ]


def get_active_job_count(
    session: Session,
    *,
    source: str,
    source_identifier: str,
) -> int:
    count = session.scalar(
        select(
            func.count(
                JobRecord.id
            )
        ).where(
            JobRecord.source
            == source,
            JobRecord.source_identifier
            == source_identifier,
            JobRecord.is_active.is_(
                True
            ),
        )
    )

    return count or 0


def build_job_upsert_values(
    jobs: list[Job],
) -> list[dict]:
    """
    Convert Job domain objects into values
    expected by the jobs table upsert.
    """

    return [
        {
            "source": (
                job.source
            ),
            "source_identifier": (
                job.source_identifier
            ),
            "external_id": (
                job.external_id
            ),
            "company": (
                job.company
            ),
            "title": (
                job.title
            ),
            "location": (
                job.location
            ),
            "department": (
                job.department
            ),
            "description": (
                job.description
            ),
            "apply_url": (
                str(
                    job.apply_url
                )
            ),
            "posted_at": (
                job.posted_at
            ),
            "source_updated_at": (
                job.updated_at
            ),
            "fingerprint": (
                job.fingerprint
            ),
            "canonical_key": (
                canonical_key(
                    company=job.company,
                    title=job.title,
                    location=job.location,
                )
            ),
            "is_active": True,
            "closed_at": None,
            "last_seen_at": (
                func.now()
            ),
        }
        for job in jobs
    ]


def execute_job_upsert_batch(
    session: Session,
    jobs: list[Job],
) -> None:
    """
    Execute one bounded PostgreSQL upsert.

    The conflict/update behavior intentionally
    matches the original repository logic.
    """

    if not jobs:
        return

    values = (
        build_job_upsert_values(
            jobs
        )
    )

    statement = insert(
        JobRecord
    ).values(
        values
    )

    statement = (
        statement.on_conflict_do_update(
            constraint=(
                "uq_job_source_external_id"
            ),
            set_={
                "company": (
                    statement.excluded.company
                ),
                "title": (
                    statement.excluded.title
                ),
                "location": (
                    statement.excluded.location
                ),
                "department": (
                    statement.excluded.department
                ),
                "description": (
                    statement.excluded.description
                ),
                "apply_url": (
                    statement.excluded.apply_url
                ),
                "posted_at": (
                    statement.excluded.posted_at
                ),
                "source_updated_at": (
                    statement.excluded
                    .source_updated_at
                ),
                "fingerprint": (
                    statement.excluded.fingerprint
                ),
                "canonical_key": (
                    statement.excluded
                    .canonical_key
                ),
                "is_active": True,
                "closed_at": None,
                "last_seen_at": (
                    func.now()
                ),
            },
        )
    )

    session.execute(
        statement
    )


def refresh_unchanged_last_seen(
    session: Session,
    *,
    source: str,
    source_identifier: str,
    external_ids: list[str],
) -> None:
    """
    Refresh last_seen_at for unchanged jobs.

    Chunking protects this path as the number
    of jobs from a single ATS/company grows.
    """

    for batch in chunked(
        external_ids,
        ID_BATCH_SIZE,
    ):
        session.execute(
            update(
                JobRecord
            )
            .where(
                JobRecord.source
                == source,
                JobRecord.source_identifier
                == source_identifier,
                JobRecord.external_id.in_(
                    batch
                ),
            )
            .values(
                last_seen_at=(
                    func.now()
                )
            )
        )


def sync_company_jobs(
    session: Session,
    jobs: list[Job],
    *,
    source: str,
    source_identifier: str,
) -> SyncResult:
    jobs_by_id = {
        job.external_id: job
        for job in jobs
    }

    current_ids = set(
        jobs_by_id
    )

    existing_rows = (
        session.execute(
            select(
                JobRecord.external_id,
                JobRecord.fingerprint,
                JobRecord.is_active,
            ).where(
                JobRecord.source
                == source,
                JobRecord.source_identifier
                == source_identifier,
            )
        ).all()
    )

    existing = {
        row.external_id: row
        for row in existing_rows
    }

    new_jobs: list[Job] = []
    changed_jobs: list[Job] = []
    reopened_jobs: list[Job] = []
    unchanged_ids: list[str] = []

    for (
        external_id,
        job,
    ) in jobs_by_id.items():
        previous = (
            existing.get(
                external_id
            )
        )

        if previous is None:
            new_jobs.append(
                job
            )
            continue

        if not previous.is_active:
            reopened_jobs.append(
                job
            )
            continue

        if (
            previous.fingerprint
            != job.fingerprint
        ):
            changed_jobs.append(
                job
            )
            continue

        unchanged_ids.append(
            external_id
        )

    jobs_to_write = (
        new_jobs
        + changed_jobs
        + reopened_jobs
    )

    # -------------------------------------------------
    # IMPORTANT:
    #
    # Previously all jobs_to_write were emitted as one
    # enormous INSERT ... ON CONFLICT statement.
    #
    # Large sources can contain thousands of jobs,
    # creating more bind parameters than PostgreSQL /
    # the driver can safely handle.
    #
    # We now keep exactly the same upsert semantics but
    # execute bounded statements.
    #
    # We deliberately DO NOT commit inside the loop.
    # The outer transaction remains atomic.
    # -------------------------------------------------

    if jobs_to_write:
        for job_batch in chunked(
            jobs_to_write,
            UPSERT_BATCH_SIZE,
        ):
            execute_job_upsert_batch(
                session,
                job_batch,
            )

    if unchanged_ids:
        refresh_unchanged_last_seen(
            session,
            source=source,
            source_identifier=(
                source_identifier
            ),
            external_ids=(
                unchanged_ids
            ),
        )

    # -------------------------------------------------
    # Close jobs that disappeared from the latest
    # source snapshot.
    #
    # current_ids is currently only a few thousand
    # values even for the largest source and therefore
    # remains comfortably below PostgreSQL's bind
    # parameter ceiling.
    #
    # This must remain one logical NOT IN condition.
    # Splitting it into multiple NOT IN updates would
    # be incorrect because each partial batch would
    # close jobs present in another batch.
    # -------------------------------------------------

    close_query = (
        update(
            JobRecord
        )
        .where(
            JobRecord.source
            == source,
            JobRecord.source_identifier
            == source_identifier,
            JobRecord.is_active.is_(
                True
            ),
        )
    )

    if current_ids:
        close_query = (
            close_query.where(
                JobRecord.external_id.not_in(
                    current_ids
                )
            )
        )

    closed_ids = (
        session.execute(
            close_query
            .values(
                is_active=False,
                closed_at=(
                    func.now()
                ),
            )
            .returning(
                JobRecord.id
            )
        )
        .scalars()
        .all()
    )

    changed_ids = {
        job.external_id
        for job in (
            new_jobs
            + changed_jobs
            + reopened_jobs
        )
    }

    return SyncResult(
        new=len(
            new_jobs
        ),
        updated=len(
            changed_jobs
        ),
        unchanged=len(
            unchanged_ids
        ),
        reopened=len(
            reopened_jobs
        ),
        closed=len(
            closed_ids
        ),
        changed_external_ids=(
            frozenset(
                changed_ids
            )
        ),
    )


def save_raw_jobs(
    session: Session,
    *,
    source: str,
    source_identifier: str,
    raw_jobs: dict[str, dict],
    external_ids: frozenset[str],
) -> None:
    if not external_ids:
        return

    records = [
        RawJobRecord(
            source=source,
            source_identifier=(
                source_identifier
            ),
            external_id=(
                external_id
            ),
            payload=(
                raw_jobs[
                    external_id
                ]
            ),
        )
        for external_id
        in external_ids
        if external_id
        in raw_jobs
    ]

    if records:
        session.add_all(
            records
        )


def save_scan(
    session: Session,
    *,
    source: str,
    source_identifier: str,
    company: str,
    success: bool,
    jobs_fetched: int,
    error_type: str | None,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    session.add(
        ScanRecord(
            source=source,
            source_identifier=(
                source_identifier
            ),
            company=company,
            success=success,
            jobs_fetched=(
                jobs_fetched
            ),
            error_type=(
                error_type
            ),
            started_at=(
                started_at
            ),
            finished_at=(
                finished_at
            ),
        )
    )