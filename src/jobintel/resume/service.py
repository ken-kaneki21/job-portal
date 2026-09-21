from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from jobintel.db.profile_repository import (
    get_universal_profile_payload,
    upsert_candidate_profile,
)
from jobintel.db.session import SessionLocal
from jobintel.profile.adapter import (
    build_legacy_candidate_profile,
)
from jobintel.profile.role_detection import (
    detect_role_families,
)
from jobintel.profile.universal import (
    CandidatePreferences,
    UniversalCandidateProfile,
)
from jobintel.resume.parser import extract_pdf_text
from jobintel.resume.skills import extract_skills
from jobintel.resume.structured import (
    extract_resume_structure,
)

logger = logging.getLogger(
    __name__,
)

PROFILE_DIR = Path(
    "profiles",
)

UNIVERSAL_PROFILE_PATH = PROFILE_DIR / "universal.json"

LEGACY_PROFILE_PATH = PROFILE_DIR / "generated_v2.json"

DEFAULT_PROFILE_NAME = "universal"


def resume_sha256(
    content: bytes,
) -> str:
    return hashlib.sha256(
        content,
    ).hexdigest()


def build_profile_from_resume(
    *,
    filename: str,
    content: bytes,
) -> UniversalCandidateProfile:
    resume_text = extract_pdf_text(
        content,
    )

    core_skills, secondary_skills = extract_skills(
        resume_text,
    )

    role_families = detect_role_families(
        resume_text,
    )

    structure = extract_resume_structure(
        resume_text,
    )

    return UniversalCandidateProfile(
        profile_name="universal",
        identity=structure.identity,
        headline=structure.headline,
        summary=structure.summary,
        total_experience_years=(structure.total_experience_years),
        role_families=role_families,
        core_skills=core_skills,
        secondary_skills=secondary_skills,
        tools=[],
        cloud_platforms=[
            skill
            for skill in (
                "Azure",
                "AWS",
                "GCP",
            )
            if skill in (core_skills + secondary_skills)
        ],
        industries=[],
        certifications=structure.certifications,
        experience=structure.experience,
        education=structure.education,
        projects=structure.projects,
        preferences=CandidatePreferences(
            preferred_locations=[
                "Bengaluru",
                "Bangalore",
                "Hyderabad",
            ],
            allowed_countries=[
                "India",
            ],
            blocked_location_terms=[],
            blocked_titles=[],
        ),
        source_resume_filename=filename,
        source_resume_sha256=resume_sha256(
            content,
        ),
    )


def write_json_file(
    path: Path,
    payload: dict,
) -> None:
    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def save_universal_profile(
    profile: UniversalCandidateProfile,
) -> None:
    write_json_file(
        UNIVERSAL_PROFILE_PATH,
        profile.model_dump(
            mode="json",
        ),
    )


def save_legacy_profile(
    profile: UniversalCandidateProfile,
) -> None:
    legacy_profile = build_legacy_candidate_profile(
        profile,
    )

    write_json_file(
        LEGACY_PROFILE_PATH,
        legacy_profile.model_dump(
            mode="json",
        ),
    )


def save_profile_compatibility_files(
    profile: UniversalCandidateProfile,
) -> None:
    try:
        save_universal_profile(
            profile,
        )

        save_legacy_profile(
            profile,
        )
    except OSError:
        logger.warning(
            (
                "Candidate profile was persisted "
                "to the database, but compatibility "
                "JSON files could not be written."
            ),
            exc_info=True,
        )


def persist_profile(
    profile: UniversalCandidateProfile,
) -> None:
    legacy_profile = build_legacy_candidate_profile(
        profile,
    )

    universal_payload = profile.model_dump(
        mode="json",
    )

    legacy_payload = legacy_profile.model_dump(
        mode="json",
    )

    with SessionLocal() as session:
        upsert_candidate_profile(
            session,
            profile_name=profile.profile_name,
            schema_version=profile.schema_version,
            universal_payload=universal_payload,
            legacy_payload=legacy_payload,
        )

        session.commit()

    save_profile_compatibility_files(
        profile,
    )


def load_universal_profile_from_file() -> UniversalCandidateProfile | None:
    if not UNIVERSAL_PROFILE_PATH.exists():
        return None

    payload = json.loads(
        UNIVERSAL_PROFILE_PATH.read_text(
            encoding="utf-8",
        ),
    )

    return UniversalCandidateProfile.model_validate(
        payload,
    )


def load_universal_profile() -> UniversalCandidateProfile | None:
    try:
        with SessionLocal() as session:
            payload = get_universal_profile_payload(
                session,
                profile_name=DEFAULT_PROFILE_NAME,
            )

        if payload is not None:
            return UniversalCandidateProfile.model_validate(
                payload,
            )

    except SQLAlchemyError:
        logger.warning(
            (
                "Unable to read candidate profile "
                "from the database; falling back "
                "to the compatibility JSON file."
            ),
            exc_info=True,
        )

    return load_universal_profile_from_file()
