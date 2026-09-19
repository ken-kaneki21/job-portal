import re

from sqlalchemy import select

from jobintel.db.company_discovery_repository import (
    enqueue_candidate,
)
from jobintel.db.models import (
    CompanyRecord,
    JobRecord,
)
from jobintel.db.session import (
    SessionLocal,
)


def normalize_company_name(
    value: str,
) -> str:
    """
    Canonical normalization used for company discovery.

    Example:
        "C&A Sourcing Jobs Asia"
        -> "c a sourcing jobs asia"

        "Calfus Inc."
        -> "calfus inc"
    """

    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def main() -> None:
    with SessionLocal() as session:
        configured_companies = {
            normalize_company_name(name)
            for name in session.scalars(select(CompanyRecord.name)).all()
            if name
        }

        broad_companies = {
            company.strip()
            for company in session.scalars(
                select(JobRecord.company)
                .where(JobRecord.source == "adzuna")
                .where(JobRecord.company.is_not(None))
            ).all()
            if company and company.strip()
        }

        eligible: list[
            tuple[
                str,
                str,
            ]
        ] = []

        for company_name in sorted(broad_companies):
            normalized = normalize_company_name(company_name)

            if not normalized:
                continue

            if normalized in configured_companies:
                continue

            eligible.append(
                (
                    company_name,
                    normalized,
                )
            )

        inserted = 0

        for (
            company_name,
            normalized_name,
        ) in eligible:
            was_inserted = enqueue_candidate(
                session,
                company_name=(company_name),
                normalized_name=(normalized_name),
            )

            if was_inserted:
                inserted += 1

        session.commit()

    print()
    print("=" * 100)
    print("COMPANY DISCOVERY QUEUE")
    print("=" * 100)

    print(f"Broad-search companies: {len(broad_companies)}")

    print(f"Eligible candidates: {len(eligible)}")

    print(f"New candidates queued: {inserted}")


if __name__ == "__main__":
    main()
