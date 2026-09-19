from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from jobintel.ats_probe_resolver import (
    resolve_company_ats,
)
from jobintel.ats_url_inspector import (
    inspect_urls_for_ats,
)
from jobintel.db.models import (
    CompanyDiscoveryCandidateRecord,
    CompanyRecord,
    JobRecord,
    JobSourceRecord,
)
from jobintel.db.session import SessionLocal


BATCH_SIZE = 20
MAX_ATTEMPTS = 1
MAX_URLS_PER_COMPANY = 10


def load_candidate_ids() -> list[int]:
    """
    Load only candidate IDs.

    Each candidate is processed later in its own
    database session/transaction so one failure cannot
    poison the entire discovery batch.
    """

    with SessionLocal() as session:
        ids = session.scalars(
            select(
                CompanyDiscoveryCandidateRecord.id
            )
            .where(
                CompanyDiscoveryCandidateRecord.status
                == "pending"
            )
            .where(
                CompanyDiscoveryCandidateRecord.attempt_count
                < MAX_ATTEMPTS
            )
            .order_by(
                CompanyDiscoveryCandidateRecord.id
            )
            .limit(
                BATCH_SIZE
            )
        ).all()

    return list(ids)


def company_exists(
    session,
    *,
    ats: str,
    identifier: str,
) -> bool:
    existing_id = session.scalar(
        select(
            CompanyRecord.id
        )
        .where(
            func.lower(
                CompanyRecord.ats
            )
            == ats.lower()
        )
        .where(
            func.lower(
                CompanyRecord.identifier
            )
            == identifier.lower()
        )
        .limit(1)
    )

    return existing_id is not None


def add_company(
    session,
    *,
    name: str,
    ats: str,
    identifier: str,
) -> bool:
    if company_exists(
        session,
        ats=ats,
        identifier=identifier,
    ):
        return False

    session.add(
        CompanyRecord(
            name=name,
            ats=ats,
            identifier=identifier,
            enabled=True,
            priority=100,
        )
    )

    return True


def load_company_urls(
    session,
    company_name: str,
) -> list[str]:
    """
    Load URLs already known for this company.

    These can come from:
    - jobs.apply_url
    - job_sources.source_url
    """

    job_rows = session.execute(
        select(
            JobRecord.id,
            JobRecord.apply_url,
        )
        .where(
            func.lower(
                func.trim(
                    JobRecord.company
                )
            )
            == company_name.lower().strip()
        )
        .order_by(
            JobRecord.id.desc()
        )
        .limit(
            MAX_URLS_PER_COMPANY
        )
    ).all()

    urls: list[str] = []
    job_ids: list[int] = []

    for job_id, apply_url in job_rows:
        job_ids.append(
            job_id
        )

        if apply_url:
            urls.append(
                apply_url
            )

    if job_ids:
        source_urls = session.scalars(
            select(
                JobSourceRecord.source_url
            )
            .where(
                JobSourceRecord.job_id.in_(
                    job_ids
                )
            )
            .where(
                JobSourceRecord.source_url
                .is_not(None)
            )
        ).all()

        for source_url in source_urls:
            if source_url:
                urls.append(
                    source_url
                )

    # Preserve order while deduplicating.
    result: list[str] = []
    seen: set[str] = set()

    for url in urls:
        value = url.strip()

        if not value:
            continue

        if value in seen:
            continue

        seen.add(
            value
        )

        result.append(
            value
        )

    return result[
        :MAX_URLS_PER_COMPANY
    ]


def resolve_candidate(
    session,
    candidate: CompanyDiscoveryCandidateRecord,
):
    """
    Resolution strategy:

    Tier 1:
        Inspect URLs we already have.

    Tier 2:
        Deterministic public ATS probing.
    """

    urls = load_company_urls(
        session,
        candidate.company_name,
    )

    if urls:
        url_result = (
            inspect_urls_for_ats(
                urls
            )
        )

        if url_result is not None:
            (
                ats,
                identifier,
                career_url,
            ) = url_result

            return (
                ats,
                identifier,
                career_url,
                "existing_url",
            )

    probe_result = (
        resolve_company_ats(
            candidate.company_name
        )
    )

    if probe_result is not None:
        return (
            probe_result.ats,
            probe_result.identifier,
            probe_result.career_url,
            "slug_probe",
        )

    return None


def mark_candidate_failed(
    candidate_id: int,
    message: str,
) -> None:
    """
    Best-effort failure status update using a brand-new
    session.

    If even this fails because the underlying candidate
    row has a database integrity issue, we log it and
    continue instead of killing the pipeline.
    """

    try:
        with SessionLocal() as session:
            candidate = session.get(
                CompanyDiscoveryCandidateRecord,
                candidate_id,
            )

            if candidate is None:
                return

            candidate.status = "failed"
            candidate.error_message = (
                message[:4000]
            )

            session.commit()

    except Exception as exc:
        print(
            "  WARNING: Could not mark "
            f"candidate {candidate_id} failed: "
            f"{exc}"
        )


def process_candidate(
    candidate_id: int,
) -> tuple[
    str,
    bool,
]:
    """
    Returns:

        (result_type, company_inserted)

    result_type:
        discovered
        unresolved
        failed
    """

    with SessionLocal() as session:
        candidate = session.get(
            CompanyDiscoveryCandidateRecord,
            candidate_id,
        )

        if candidate is None:
            return (
                "failed",
                False,
            )

        if candidate.status != "pending":
            return (
                "failed",
                False,
            )

        print()
        print(
            f"[{candidate.id}] "
            f"{candidate.company_name}"
        )

        candidate.attempt_count += 1

        candidate.last_attempt_at = (
            datetime.now(
                timezone.utc
            )
        )

        try:
            resolution = (
                resolve_candidate(
                    session,
                    candidate,
                )
            )

            if resolution is None:
                candidate.status = (
                    "unsupported"
                )

                candidate.error_message = (
                    "No supported ATS found "
                    "using existing URLs or "
                    "deterministic probe resolver."
                )

                session.commit()

                print(
                    "  No supported ATS found."
                )

                return (
                    "unresolved",
                    False,
                )

            (
                ats,
                identifier,
                career_url,
                method,
            ) = resolution

            candidate.status = (
                "discovered"
            )

            candidate.discovered_ats = (
                ats
            )

            candidate.discovered_identifier = (
                identifier
            )

            candidate.career_url = (
                career_url
            )

            candidate.error_message = None

            added = add_company(
                session,
                name=candidate.company_name,
                ats=ats,
                identifier=identifier,
            )

            session.commit()

            print(
                f"  Method: {method}"
            )

            print(
                f"  ATS: {ats}"
            )

            print(
                f"  Identifier: {identifier}"
            )

            print(
                f"  URL: {career_url}"
            )

            print(
                f"  Added to companies: "
                f"{added}"
            )

            return (
                "discovered",
                added,
            )

        except IntegrityError as exc:
            # Absolutely required after any failed flush
            # or commit.
            session.rollback()

            print(
                "  DATABASE INTEGRITY ERROR: "
                f"{exc.orig}"
            )

            return (
                "failed",
                False,
            )

        except Exception as exc:
            session.rollback()

            print(
                f"  ERROR: {exc}"
            )

            return (
                "failed",
                False,
            )


def main() -> None:
    candidate_ids = (
        load_candidate_ids()
    )

    if not candidate_ids:
        print()
        print(
            "No pending company discovery "
            "candidates."
        )
        return

    print()
    print("=" * 100)
    print(
        "FREE ATS DISCOVERY"
    )
    print("=" * 100)

    processed = 0
    discovered = 0
    inserted = 0
    unresolved = 0
    failed = 0

    for candidate_id in candidate_ids:
        processed += 1

        try:
            (
                result_type,
                company_inserted,
            ) = process_candidate(
                candidate_id
            )

            if (
                result_type
                == "discovered"
            ):
                discovered += 1

                if company_inserted:
                    inserted += 1

            elif (
                result_type
                == "unresolved"
            ):
                unresolved += 1

            else:
                failed += 1

                mark_candidate_failed(
                    candidate_id,
                    (
                        "Candidate processing "
                        "failed. See pipeline logs."
                    ),
                )

        except Exception as exc:
            failed += 1

            print()
            print(
                f"[{candidate_id}] "
                f"UNHANDLED ERROR: {exc}"
            )

            mark_candidate_failed(
                candidate_id,
                str(
                    exc
                ),
            )

    print()
    print("=" * 100)
    print(
        "ATS DISCOVERY SUMMARY"
    )
    print("=" * 100)

    print(
        f"Processed:       "
        f"{processed}"
    )

    print(
        f"Discovered:      "
        f"{discovered}"
    )

    print(
        f"Companies added: "
        f"{inserted}"
    )

    print(
        f"Unresolved:      "
        f"{unresolved}"
    )

    print(
        f"Errors:          "
        f"{failed}"
    )


if __name__ == "__main__":
    main()