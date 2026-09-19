import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from jobintel.company_registry import load_companies
from jobintel.db.repository import (
    SyncResult,
    get_active_job_count,
    save_raw_jobs,
    save_scan,
    sync_company_jobs,
)
from jobintel.db.session import SessionLocal
from jobintel.models.company import Company
from jobintel.models.fetched_job import FetchedJob
from jobintel.sources.base import JobSource
from jobintel.sources.registry import build_sources


MAX_CONCURRENCY = 5

MIN_SAFE_JOB_RATIO = 0.40


@dataclass(frozen=True)
class CompanyScan:
    company: Company
    fetched_jobs: list[FetchedJob]
    success: bool
    error_type: str | None
    started_at: datetime
    finished_at: datetime


async def fetch_company(
    source: JobSource,
    company: Company,
    semaphore: asyncio.Semaphore,
) -> CompanyScan:
    started_at = datetime.now(
        timezone.utc
    )

    async with semaphore:
        try:
            fetched_jobs = await source.fetch_jobs(
                company
            )

            finished_at = datetime.now(
                timezone.utc
            )

            print(
                f"{company.name:<25}"
                f"{len(fetched_jobs):>5} jobs"
            )

            return CompanyScan(
                company=company,
                fetched_jobs=fetched_jobs,
                success=True,
                error_type=None,
                started_at=started_at,
                finished_at=finished_at,
            )

        except httpx.HTTPError as exc:
            finished_at = datetime.now(
                timezone.utc
            )

            print(
                f"{company.name:<25}"
                f"FAILED: {type(exc).__name__}"
            )

            return CompanyScan(
                company=company,
                fetched_jobs=[],
                success=False,
                error_type=type(exc).__name__,
                started_at=started_at,
                finished_at=finished_at,
            )


def add_results(
    left: SyncResult,
    right: SyncResult,
) -> SyncResult:
    return SyncResult(
        new=left.new + right.new,
        updated=left.updated + right.updated,
        unchanged=left.unchanged + right.unchanged,
        reopened=left.reopened + right.reopened,
        closed=left.closed + right.closed,
        changed_external_ids=(
            left.changed_external_ids
            | right.changed_external_ids
        ),
    )


async def main() -> None:
    companies = load_companies()

    semaphore = asyncio.Semaphore(
        MAX_CONCURRENCY
    )

    timeout = httpx.Timeout(20.0)

    limits = httpx.Limits(
        max_connections=10,
        max_keepalive_connections=5,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
    ) as client:
        sources = build_sources(client)

        tasks = []

        for company in companies:
            if not company.enabled:
                continue

            source = sources.get(
                company.ats
            )

            if source is None:
                print(
                    f"{company.name:<25}"
                    f"FAILED: unsupported ATS "
                    f"'{company.ats}'"
                )

                continue

            tasks.append(
                fetch_company(
                    source=source,
                    company=company,
                    semaphore=semaphore,
                )
            )

        scans = await asyncio.gather(
            *tasks
        )

    total = SyncResult()

    fetched = 0
    successful_scans = 0

    with SessionLocal() as session:
        for scan in scans:
            jobs = [
                item.job
                for item in scan.fetched_jobs
            ]

            effective_success = (
                scan.success
            )

            error_type = (
                scan.error_type
            )

            if scan.success:
                previous_active = (
                    get_active_job_count(
                        session=session,
                        source=scan.company.ats,
                        source_identifier=(
                            scan.company.identifier
                        ),
                    )
                )

                current_count = len(
                    jobs
                )

                suspicious_drop = (
                    previous_active > 0
                    and current_count
                    < (
                        previous_active
                        * MIN_SAFE_JOB_RATIO
                    )
                )

                if suspicious_drop:
                    effective_success = False

                    error_type = (
                        "SuspiciousJobCountDrop"
                    )

                    print(
                        f"{scan.company.name:<25}"
                        f"SKIPPED SYNC: "
                        f"{previous_active} "
                        f"-> {current_count}"
                    )

            save_scan(
                session=session,
                source=scan.company.ats,
                source_identifier=(
                    scan.company.identifier
                ),
                company=scan.company.name,
                success=effective_success,
                jobs_fetched=len(jobs),
                error_type=error_type,
                started_at=scan.started_at,
                finished_at=scan.finished_at,
            )

            if not effective_success:
                continue

            successful_scans += 1

            fetched += len(jobs)

            result = sync_company_jobs(
                session=session,
                jobs=jobs,
                source=scan.company.ats,
                source_identifier=(
                    scan.company.identifier
                ),
            )

            raw_jobs = {
                item.job.external_id:
                    item.raw
                for item
                in scan.fetched_jobs
            }

            save_raw_jobs(
                session=session,
                source=scan.company.ats,
                source_identifier=(
                    scan.company.identifier
                ),
                raw_jobs=raw_jobs,
                external_ids=(
                    result.changed_external_ids
                ),
            )

            total = add_results(
                total,
                result,
            )

        session.commit()

    print()
    print(
        f"Companies configured: "
        f"{len(companies)}"
    )

    print(
        f"Successful scans:     "
        f"{successful_scans}"
    )

    print(
        f"Jobs fetched:         "
        f"{fetched}"
    )

    print()
    print("Database:")

    print(
        f"New:                  "
        f"{total.new}"
    )

    print(
        f"Updated:              "
        f"{total.updated}"
    )

    print(
        f"Unchanged:            "
        f"{total.unchanged}"
    )

    print(
        f"Reopened:             "
        f"{total.reopened}"
    )

    print(
        f"Closed:               "
        f"{total.closed}"
    )


if __name__ == "__main__":
    asyncio.run(main())