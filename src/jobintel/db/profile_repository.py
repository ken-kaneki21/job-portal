from __future__ import annotations

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from jobintel.db.profile_models import (
    CandidateProfileRecord,
)


def upsert_candidate_profile(
    session: Session,
    *,
    profile_name: str,
    schema_version: str,
    universal_payload: dict,
    legacy_payload: dict,
) -> CandidateProfileRecord:
    statement = (
        insert(
            CandidateProfileRecord,
        )
        .values(
            profile_name=profile_name,
            schema_version=schema_version,
            universal_payload=universal_payload,
            legacy_payload=legacy_payload,
        )
        .on_conflict_do_update(
            index_elements=[
                CandidateProfileRecord.profile_name,
            ],
            set_={
                "schema_version": schema_version,
                "universal_payload": universal_payload,
                "legacy_payload": legacy_payload,
                "updated_at": func.now(),
            },
        )
        .returning(
            CandidateProfileRecord,
        )
    )

    record = session.scalar(
        statement,
    )

    if record is None:
        raise RuntimeError("Candidate profile upsert did not return a record.")

    return record


def get_candidate_profile(
    session: Session,
    *,
    profile_name: str,
) -> CandidateProfileRecord | None:
    return session.scalar(
        select(
            CandidateProfileRecord,
        ).where(CandidateProfileRecord.profile_name == profile_name)
    )


def get_universal_profile_payload(
    session: Session,
    *,
    profile_name: str,
) -> dict | None:
    record = get_candidate_profile(
        session,
        profile_name=profile_name,
    )

    if record is None:
        return None

    return dict(
        record.universal_payload,
    )


def get_legacy_profile_payload(
    session: Session,
    *,
    profile_name: str,
) -> dict | None:
    record = get_candidate_profile(
        session,
        profile_name=profile_name,
    )

    if record is None:
        return None

    return dict(
        record.legacy_payload,
    )
