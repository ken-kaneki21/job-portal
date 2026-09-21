from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from jobintel.db.broad_repository import (
    persist_broad_jobs,
)
from jobintel.db.session import SessionLocal
from jobintel.models.fetched_job import FetchedJob
from jobintel.profile.loader import load_profile
from jobintel.profile.models import CandidateProfile
from jobintel.profile.runtime import (
    ACTIVE_PROFILE_PATH,
)
from jobintel.search_sources.adzuna import (
    AdzunaSource,
)

MAX_PAGES = 2

MAX_SEARCHES = 12
PRIMARY_ROLE_LIMIT = 6
ADJACENT_ROLE_LIMIT = 3
SKILL_QUERY_LIMIT = 3

DEFAULT_LOCATION = "India"

LOCATION_ALIASES = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "hyderabad": "Hyderabad",
    "india": "India",
}


@dataclass(frozen=True)
class SearchSpec:
    query: str
    location: str


def normalize_text(
    value: str,
) -> str:
    return " ".join(value.strip().split())


def normalize_location(
    value: str,
) -> str:
    cleaned = normalize_text(value)

    if not cleaned:
        return DEFAULT_LOCATION

    return LOCATION_ALIASES.get(
        cleaned.lower(),
        cleaned,
    )


def unique_strings(
    values: list[str],
) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        cleaned = normalize_text(value)

        if not cleaned:
            continue

        key = cleaned.lower()

        if key in seen:
            continue

        seen.add(key)
        output.append(cleaned)

    return output


def preferred_search_locations(
    profile: CandidateProfile,
) -> list[str]:
    locations = [
        normalize_location(location)
        for location in profile.preferred_locations
        if location.strip()
    ]

    locations = unique_strings(locations)

    city_locations = [location for location in locations if location.lower() != "india"]

    if city_locations:
        return city_locations

    return [DEFAULT_LOCATION]


def country_search_location(
    profile: CandidateProfile,
) -> str:
    for country in profile.allowed_countries:
        cleaned = normalize_location(country)

        if cleaned:
            return cleaned

    return DEFAULT_LOCATION


def add_search(
    searches: list[SearchSpec],
    seen: set[tuple[str, str]],
    *,
    query: str,
    location: str,
) -> None:
    if len(searches) >= MAX_SEARCHES:
        return

    normalized_query = normalize_text(query)

    normalized_location = normalize_location(location)

    if not normalized_query:
        return

    key = (
        normalized_query.lower(),
        normalized_location.lower(),
    )

    if key in seen:
        return

    seen.add(key)

    searches.append(
        SearchSpec(
            query=normalized_query,
            location=normalized_location,
        )
    )


def build_profile_searches(
    profile: CandidateProfile,
) -> list[SearchSpec]:
    searches: list[SearchSpec] = []

    seen: set[tuple[str, str]] = set()

    primary_titles = unique_strings(profile.target_titles)[:PRIMARY_ROLE_LIMIT]

    adjacent_titles = unique_strings(profile.adjacent_titles)[:ADJACENT_ROLE_LIMIT]

    locations = preferred_search_locations(profile)

    country = country_search_location(profile)

    # -------------------------------------------------
    # 1. Primary role searches
    #
    # Give each primary title one preferred city.
    # Locations rotate instead of creating a full
    # role x city matrix.
    # -------------------------------------------------

    for index, title in enumerate(primary_titles):
        location = locations[index % len(locations)]

        add_search(
            searches,
            seen,
            query=title,
            location=location,
        )

    # -------------------------------------------------
    # 2. Adjacent role discovery
    #
    # Adjacent roles search country-wide so they add
    # useful breadth without multiplying API calls.
    # -------------------------------------------------

    for title in adjacent_titles:
        add_search(
            searches,
            seen,
            query=title,
            location=country,
        )

    # -------------------------------------------------
    # 3. Skill-enhanced searches
    #
    # Add only a few high-value skill + primary-role
    # searches. This replaces old hardcoded queries
    # such as "snowflake data engineer".
    # -------------------------------------------------

    anchor_title = (
        primary_titles[0]
        if primary_titles
        else (adjacent_titles[0] if adjacent_titles else "")
    )

    if anchor_title:
        skills = unique_strings(profile.core_skills)

        skill_queries_added = 0

        for skill in skills:
            if skill_queries_added >= SKILL_QUERY_LIMIT:
                break

            if skill.lower() in anchor_title.lower():
                continue

            before = len(searches)

            add_search(
                searches,
                seen,
                query=(f"{skill} {anchor_title}"),
                location=country,
            )

            if len(searches) > before:
                skill_queries_added += 1

    # -------------------------------------------------
    # 4. Fallback
    # -------------------------------------------------

    if not searches:
        add_search(
            searches,
            seen,
            query="data engineer",
            location=country,
        )

    return searches[:MAX_SEARCHES]


def load_active_search_profile() -> CandidateProfile:
    return load_profile(ACTIVE_PROFILE_PATH)


async def fetch_jobs(
    searches: list[SearchSpec],
) -> list[FetchedJob]:
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
        source = AdzunaSource(
            client,
            country="in",
        )

        all_jobs: list[FetchedJob] = []

        for index, search in enumerate(
            searches,
            start=1,
        ):
            print(
                f"[{index:02d}/"
                f"{len(searches):02d}] "
                f"{search.query:<35} "
                f"{search.location:<15}",
                end="",
                flush=True,
            )

            jobs = await source.search_jobs(
                query=search.query,
                location=search.location,
                max_pages=MAX_PAGES,
            )

            print(f"{len(jobs):>5} jobs")

            all_jobs.extend(jobs)

    return all_jobs


def deduplicate_source_jobs(
    fetched_jobs: list[FetchedJob],
) -> list[FetchedJob]:
    unique: dict[
        tuple[
            str,
            str | None,
            str | None,
        ],
        FetchedJob,
    ] = {}

    for item in fetched_jobs:
        job = item.job

        key = (
            job.source,
            job.source_identifier,
            job.external_id,
        )

        unique[key] = item

    return list(unique.values())


def print_search_plan(
    profile: CandidateProfile,
    searches: list[SearchSpec],
) -> None:
    print()

    print("=" * 100)

    print("PROFILE-DRIVEN BROAD SEARCH")

    print("=" * 100)

    print(f"Profile: {profile.name}")

    print(f"Profile path: {ACTIVE_PROFILE_PATH}")

    print(f"Searches: {len(searches)}")

    print(f"Max pages/search: {MAX_PAGES}")

    print()

    for index, search in enumerate(
        searches,
        start=1,
    ):
        print(f"{index:02d}. {search.query:<40} | {search.location}")


async def main() -> None:
    profile = load_active_search_profile()

    searches = build_profile_searches(profile)

    print_search_plan(
        profile,
        searches,
    )

    fetched_jobs = await fetch_jobs(searches)

    unique_jobs = deduplicate_source_jobs(fetched_jobs)

    print()

    print(f"Fetched:       {len(fetched_jobs)}")

    print(f"Source unique: {len(unique_jobs)}")

    with SessionLocal() as session:
        result = persist_broad_jobs(
            session=session,
            fetched_jobs=unique_jobs,
        )

        session.commit()

    print()

    print("Database:")

    print(f"New canonical jobs: {result.new}")

    print(f"Matched existing:   {result.matched_existing}")

    print(f"Already known:      {result.existing_source}")

    print(f"Raw payloads saved: {result.raw_saved}")


if __name__ == "__main__":
    asyncio.run(main())
