from urllib.parse import urlparse

from sqlalchemy import select

from jobintel.db.models import (
    CompanyRecord,
    JobRecord,
    JobSourceRecord,
)
from jobintel.db.session import SessionLocal

SUPPORTED_ATS = {
    "greenhouse",
    "lever",
    "ashby",
    "smartrecruiters",
}


def clean_path_parts(
    url: str,
) -> list[str]:
    parsed = urlparse(url.strip())

    return [part for part in parsed.path.split("/") if part]


def detect_ats(
    url: str,
) -> tuple[str, str] | None:
    """
    Return:
        (ats, identifier)

    Supported:
        Greenhouse
        Lever
        Ashby
        SmartRecruiters
    """

    if not url:
        return None

    try:
        parsed = urlparse(url.strip())

        host = parsed.netloc.lower().split(":")[0]

        parts = clean_path_parts(url)

        # ---------------------------------------------
        # Greenhouse
        # ---------------------------------------------

        greenhouse_hosts = {
            "boards.greenhouse.io",
            "job-boards.greenhouse.io",
        }

        if host in greenhouse_hosts:
            if not parts:
                return None

            identifier = parts[0]

            return (
                "greenhouse",
                identifier,
            )

        # ---------------------------------------------
        # Lever
        # ---------------------------------------------

        if host == "jobs.lever.co":
            if not parts:
                return None

            identifier = parts[0]

            return (
                "lever",
                identifier,
            )

        # ---------------------------------------------
        # Ashby
        # ---------------------------------------------

        if host == "jobs.ashbyhq.com":
            if not parts:
                return None

            identifier = parts[0]

            return (
                "ashby",
                identifier,
            )

        # ---------------------------------------------
        # SmartRecruiters
        # ---------------------------------------------

        smartrecruiters_hosts = {
            "jobs.smartrecruiters.com",
            "careers.smartrecruiters.com",
        }

        if host in smartrecruiters_hosts:
            if not parts:
                return None

            identifier = parts[0]

            return (
                "smartrecruiters",
                identifier,
            )

    except Exception:
        return None

    return None


def load_existing_companies(
    session,
) -> set[tuple[str, str]]:
    rows = session.execute(
        select(
            CompanyRecord.ats,
            CompanyRecord.identifier,
        )
    ).all()

    return {
        (
            ats.lower(),
            identifier.lower(),
        )
        for ats, identifier in rows
    }


def discover_from_jobs(
    session,
) -> dict[
    tuple[str, str],
    str,
]:
    """
    Returns mapping:

        (ats, identifier) -> company name
    """

    discovered: dict[
        tuple[str, str],
        str,
    ] = {}

    rows = session.execute(
        select(
            JobRecord.company,
            JobRecord.apply_url,
        ).where(JobRecord.apply_url.is_not(None))
    ).all()

    for company, url in rows:
        result = detect_ats(url)

        if result is None:
            continue

        ats, identifier = result

        key = (
            ats.lower(),
            identifier.lower(),
        )

        discovered.setdefault(
            key,
            company,
        )

    return discovered


def discover_from_job_sources(
    session,
) -> dict[
    tuple[str, str],
    str,
]:
    discovered: dict[
        tuple[str, str],
        str,
    ] = {}

    rows = session.execute(
        select(
            JobRecord.company,
            JobSourceRecord.source_url,
        )
        .join(
            JobRecord,
            JobRecord.id == JobSourceRecord.job_id,
        )
        .where(JobSourceRecord.source_url.is_not(None))
    ).all()

    for company, url in rows:
        result = detect_ats(url)

        if result is None:
            continue

        ats, identifier = result

        key = (
            ats.lower(),
            identifier.lower(),
        )

        discovered.setdefault(
            key,
            company,
        )

    return discovered


def main() -> None:
    with SessionLocal() as session:
        existing = load_existing_companies(session)

        discovered = {}

        discovered.update(discover_from_jobs(session))

        discovered.update(discover_from_job_sources(session))

        candidates = {
            key: company for key, company in discovered.items() if key not in existing
        }

        inserted = 0

        for (
            ats,
            identifier,
        ), company_name in sorted(candidates.items()):
            if ats not in SUPPORTED_ATS:
                continue

            record = CompanyRecord(
                name=company_name,
                ats=ats,
                identifier=identifier,
                enabled=True,
                priority=100,
            )

            session.add(record)

            inserted += 1

            print(f"Discovered: {company_name} | {ats} | {identifier}")

        session.commit()

    print()
    print("=" * 100)
    print("ATS COMPANY DISCOVERY")
    print("=" * 100)

    print(f"Detected ATS identities: {len(discovered)}")

    print(f"Already configured: {len(discovered) - inserted}")

    print(f"New companies inserted: {inserted}")


if __name__ == "__main__":
    main()
