from __future__ import annotations

import hashlib
import json
from pathlib import Path

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
from jobintel.resume.parser import (
    extract_pdf_text,
)
from jobintel.resume.skills import (
    extract_skills,
)

PROFILE_DIR = Path(
    "profiles",
)

UNIVERSAL_PROFILE_PATH = PROFILE_DIR / "universal.json"

LEGACY_PROFILE_PATH = PROFILE_DIR / "generated_v2.json"


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

    profile = UniversalCandidateProfile(
        profile_name="universal",
        headline=None,
        summary=None,
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

    return profile


def save_universal_profile(
    profile: UniversalCandidateProfile,
) -> None:
    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    UNIVERSAL_PROFILE_PATH.write_text(
        json.dumps(
            profile.model_dump(
                mode="json",
            ),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def save_legacy_profile(
    profile: UniversalCandidateProfile,
) -> None:
    legacy_profile = build_legacy_candidate_profile(
        profile,
    )

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    LEGACY_PROFILE_PATH.write_text(
        json.dumps(
            legacy_profile.model_dump(),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def persist_profile(
    profile: UniversalCandidateProfile,
) -> None:
    save_universal_profile(
        profile,
    )

    save_legacy_profile(
        profile,
    )


def load_universal_profile() -> UniversalCandidateProfile | None:
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
