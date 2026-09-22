from __future__ import annotations

from jobintel.profile.models import CandidateProfile
from jobintel.profile.universal import UniversalCandidateProfile

DEFAULT_EXCLUDED_TITLES = [
    "director",
    "vice president",
    "vp",
    "principal",
    "staff",
    "architect",
    "head of",
]

ROLE_TITLE_MAP: dict[str, list[str]] = {
    "Data Engineer": [
        "data engineer",
        "senior data engineer",
        "data engineering",
    ],
    "Analytics Engineer": [
        "analytics engineer",
    ],
    "Data Analyst": [
        "data analyst",
        "senior data analyst",
        "business data analyst",
    ],
    "AI Engineer": [
        "ai engineer",
        "artificial intelligence engineer",
    ],
    "GenAI Engineer": [
        "genai engineer",
        "generative ai engineer",
        "llm engineer",
    ],
    "ML Engineer": [
        "machine learning engineer",
        "ml engineer",
    ],
    "Data Platform Engineer": [
        "data platform engineer",
        "platform data engineer",
    ],
    "Cloud Data Engineer": [
        "cloud data engineer",
    ],
}


def unique_strings(
    values: list[str],
) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        cleaned = value.strip()

        if not cleaned:
            continue

        lowered = cleaned.lower()

        if lowered in seen:
            continue

        seen.add(lowered)
        output.append(cleaned)

    return output


def build_legacy_candidate_profile(
    profile: UniversalCandidateProfile,
) -> CandidateProfile:
    enabled_roles = [role for role in profile.role_families if role.enabled]

    target_titles: list[str] = []
    adjacent_titles: list[str] = []

    for role in enabled_roles:
        titles = ROLE_TITLE_MAP.get(
            role.name,
            [],
        )

        if role.priority == "primary":
            target_titles.extend(titles)
        else:
            adjacent_titles.extend(titles)

    if not target_titles and adjacent_titles:
        target_titles = adjacent_titles[:]
        adjacent_titles = []

    experience_years = (
        profile.total_experience_years
        if profile.total_experience_years is not None
        else 5.0
    )

    preferred_max = max(
        5,
        int(round(experience_years + 2)),
    )

    hard_max = max(
        preferred_max + 3,
        8,
    )

    preferences = profile.preferences

    return CandidateProfile(
        name=profile.profile_name,
        target_titles=unique_strings(target_titles),
        adjacent_titles=unique_strings(adjacent_titles),
        exclude_titles=unique_strings(
            preferences.blocked_titles or DEFAULT_EXCLUDED_TITLES,
        ),
        preferred_locations=unique_strings(
            preferences.preferred_locations,
        ),
        allowed_countries=unique_strings(
            preferences.allowed_countries,
        ),
        blocked_location_terms=unique_strings(
            preferences.blocked_location_terms,
        ),
        core_skills=unique_strings(
            profile.core_skills,
        ),
        secondary_skills=unique_strings(
            profile.secondary_skills + profile.tools + profile.cloud_platforms,
        ),
        max_preferred_experience_years=preferred_max,
        hard_max_experience_years=hard_max,
    )
