from sqlalchemy.dialects.postgresql import insert

from jobintel.db.models import (
    CompanyDiscoveryCandidateRecord,
)


def enqueue_candidate(
    session,
    *,
    company_name: str,
    normalized_name: str,
) -> bool:
    """
    Insert a company discovery candidate exactly once.

    PostgreSQL is the authority for deduplication.

    Returns:
        True  -> row inserted
        False -> normalized company already existed
    """

    stmt = (
        insert(
            CompanyDiscoveryCandidateRecord
        )
        .values(
            company_name=company_name,
            normalized_name=normalized_name,
            status="pending",
            attempt_count=0,
        )
        .on_conflict_do_nothing(
            index_elements=[
                "normalized_name",
            ]
        )
        .returning(
            CompanyDiscoveryCandidateRecord.id
        )
    )

    inserted_id = session.scalar(
        stmt
    )

    return inserted_id is not None