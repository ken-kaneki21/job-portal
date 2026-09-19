import asyncio

import httpx

from jobintel.db.broad_repository import (
    persist_broad_jobs,
)
from jobintel.db.session import SessionLocal
from jobintel.search_sources.adzuna import (
    AdzunaSource,
)


SEARCHES = [
    {
        "query": "data engineer",
        "location": "Bangalore",
    },
    {
        "query": "data engineer",
        "location": "Hyderabad",
    },
    {
        "query": "analytics engineer",
        "location": "India",
    },
    {
        "query": "data platform engineer",
        "location": "India",
    },
    {
        "query": "snowflake data engineer",
        "location": "India",
    },
    {
        "query": "databricks data engineer",
        "location": "India",
    },
    {
        "query": "pyspark data engineer",
        "location": "India",
    },
]


MAX_PAGES = 2


async def fetch_jobs() -> list:
    timeout = httpx.Timeout(
        20.0
    )

    limits = httpx.Limits(
        max_connections=10,
        max_keepalive_connections=5,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
    ) as client:
        source = AdzunaSource(
            client,
            country="in",
        )

        all_jobs = []

        for search in SEARCHES:
            jobs = await source.search_jobs(
                query=search["query"],
                location=search["location"],
                max_pages=MAX_PAGES,
            )

            print(
                f"{search['query']:<30}"
                f"{search['location']:<15}"
                f"{len(jobs):>5} jobs"
            )

            all_jobs.extend(
                jobs
            )

    return all_jobs


def deduplicate_source_jobs(
    fetched_jobs: list,
) -> list:
    unique = {}

    for item in fetched_jobs:
        job = item.job

        key = (
            job.source,
            job.source_identifier,
            job.external_id,
        )

        unique[key] = item

    return list(
        unique.values()
    )


async def main() -> None:
    fetched_jobs = await fetch_jobs()

    unique_jobs = deduplicate_source_jobs(
        fetched_jobs
    )

    print()
    print(
        f"Fetched:       "
        f"{len(fetched_jobs)}"
    )

    print(
        f"Source unique: "
        f"{len(unique_jobs)}"
    )

    with SessionLocal() as session:
        result = persist_broad_jobs(
            session=session,
            fetched_jobs=unique_jobs,
        )

        session.commit()

    print()
    print("Database:")

    print(
        f"New canonical jobs: "
        f"{result.new}"
    )

    print(
        f"Matched existing:   "
        f"{result.matched_existing}"
    )

    print(
        f"Already known:      "
        f"{result.existing_source}"
    )

    print(
        f"Raw payloads saved: "
        f"{result.raw_saved}"
    )


if __name__ == "__main__":
    asyncio.run(main())