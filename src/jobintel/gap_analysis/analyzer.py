from dataclasses import asdict, dataclass
from typing import Any

ANALYZER_VERSION = "deterministic_gap_v2"


SKILL_ALIASES = {
    "adf": "azure data factory",
    "azure data factory": "azure data factory",
    "py spark": "pyspark",
    "pyspark": "pyspark",
    "apache spark": "spark",
    "spark": "spark",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "powerbi": "power bi",
    "power bi": "power bi",
    "amazon web services": "aws",
    "aws": "aws",
    "microsoft azure": "azure",
    "azure": "azure",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "gcp": "gcp",
    "data build tool": "dbt",
    "dbt": "dbt",
}


@dataclass(frozen=True)
class GapAnalysis:
    matched_required_skills: list[str]
    missing_required_skills: list[str]

    matched_preferred_skills: list[str]
    missing_preferred_skills: list[str]

    matched_platforms: list[str]
    missing_platforms: list[str]

    deal_breakers: list[str]

    experience_fit: str
    experience_gap_years: float | None

    required_skill_match_ratio: float
    preferred_skill_match_ratio: float
    platform_match_ratio: float

    gap_score: float

    fit_summary: str

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_skill(
    value: str,
) -> str:
    normalized = value.strip().lower()

    return SKILL_ALIASES.get(
        normalized,
        normalized,
    )


def normalize_collection(
    values: list[str] | tuple[str, ...] | None,
) -> set[str]:
    if not values:
        return set()

    return {normalize_skill(value) for value in values if value and value.strip()}


def get_profile_skills(
    profile: Any,
) -> set[str]:
    skills: set[str] = set()

    for attribute in (
        "core_skills",
        "secondary_skills",
    ):
        values = getattr(
            profile,
            attribute,
            None,
        )

        skills.update(normalize_collection(values))

    return skills


def get_profile_experience(
    profile: Any,
) -> float | None:
    """
    Only use explicit actual experience
    stored in the profile.

    Search preference limits are NOT
    candidate experience.
    """

    for attribute in (
        "experience_years",
        "years_of_experience",
        "total_experience_years",
    ):
        value = getattr(
            profile,
            attribute,
            None,
        )

        if value is None:
            continue

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


def calculate_ratio(
    matched: set[str],
    expected: set[str],
) -> float:
    """
    Empty requirements are unknown,
    not a perfect match.
    """

    if not expected:
        return 0.0

    return round(
        len(matched) / len(expected),
        4,
    )


def analyze_experience(
    *,
    required_years: int | None,
    profile_experience: float | None,
) -> tuple[
    str,
    float | None,
]:
    if required_years is None:
        return (
            "not_specified",
            None,
        )

    if profile_experience is None:
        return (
            "unknown",
            None,
        )

    gap = profile_experience - float(required_years)

    if gap >= 0:
        return (
            "meets",
            0.0,
        )

    return (
        "below_requirement",
        round(
            abs(gap),
            1,
        ),
    )


def calculate_gap_score(
    *,
    required_skills: set[str],
    required_ratio: float,
    preferred_skills: set[str],
    preferred_ratio: float,
    platforms: set[str],
    platform_ratio: float,
    required_experience: int | None,
    experience_fit: str,
    deal_breakers: list[str],
) -> float:
    """
    Evidence-aware fit score.

    Missing JD information does not
    count as a perfect match.

    Available evidence:
      required skills   55
      preferred skills  10
      platforms         15
      experience        15
      deal breakers      5

    We score only dimensions that are
    actually present, then apply an
    evidence-confidence adjustment so
    sparse JDs cannot automatically
    score 100.
    """

    earned = 0.0
    available = 0.0

    # Required skills
    if required_skills:
        available += 55.0

        earned += required_ratio * 55.0

    # Preferred skills
    if preferred_skills:
        available += 10.0

        earned += preferred_ratio * 10.0

    # Platforms
    if platforms:
        available += 15.0

        earned += platform_ratio * 15.0

    # Experience
    if required_experience is not None:
        available += 15.0

        if experience_fit == "meets":
            earned += 15.0

        elif experience_fit == "unknown":
            # Unknown candidate YOE should
            # neither look perfect nor fail.
            earned += 7.5

        elif experience_fit == "below_requirement":
            earned += 0.0

    # Deal breakers are always observable.
    available += 5.0

    if not deal_breakers:
        earned += 5.0

    if available <= 0:
        return 50.0

    evidence_fit = (earned / available) * 100.0

    # How much useful JD evidence was
    # actually available?
    evidence_coverage = min(
        1.0,
        available / 100.0,
    )

    # Sparse jobs gravitate toward neutral
    # rather than incorrectly becoming 100.
    adjusted = evidence_fit * (0.5 + 0.5 * evidence_coverage)

    # Truly empty JDs should be neutral.
    has_real_requirements = any(
        (
            bool(required_skills),
            bool(preferred_skills),
            bool(platforms),
            required_experience is not None,
        )
    )

    if not has_real_requirements:
        adjusted = 50.0

    return round(
        min(
            100.0,
            max(
                0.0,
                adjusted,
            ),
        ),
        2,
    )


def build_fit_summary(
    *,
    required_skills: set[str],
    matched_required: set[str],
    missing_required: set[str],
    preferred_skills: set[str],
    matched_preferred: set[str],
    missing_preferred: set[str],
    platforms: set[str],
    matched_platforms: set[str],
    missing_platforms: set[str],
    required_experience: int | None,
    experience_fit: str,
    experience_gap_years: float | None,
    deal_breakers: list[str],
    gap_score: float,
) -> str:
    parts: list[str] = []

    if required_skills:
        if matched_required:
            parts.append("Matched required: " + ", ".join(sorted(matched_required)))

        if missing_required:
            parts.append("Missing required: " + ", ".join(sorted(missing_required)))

    else:
        parts.append("Required skills not clearly specified")

    if preferred_skills:
        if matched_preferred:
            parts.append("Matched preferred: " + ", ".join(sorted(matched_preferred)))

        if missing_preferred:
            parts.append("Missing preferred: " + ", ".join(sorted(missing_preferred)))

    if platforms:
        if matched_platforms:
            parts.append("Matched platforms: " + ", ".join(sorted(matched_platforms)))

        if missing_platforms:
            parts.append("Missing platforms: " + ", ".join(sorted(missing_platforms)))

    if required_experience is None:
        parts.append("Experience requirement not specified")

    elif experience_fit == "meets":
        parts.append("Experience requirement met")

    elif experience_fit == "unknown":
        parts.append("Candidate experience not explicitly stored in profile")

    elif experience_fit == "below_requirement":
        parts.append(f"Experience gap: {experience_gap_years} years")

    if deal_breakers:
        parts.append("Potential deal-breakers: " + ", ".join(sorted(deal_breakers)))

    parts.append(f"Gap fit score: {gap_score:.1f}/100")

    return " | ".join(parts)


def analyze_job_gap(
    *,
    profile: Any,
    enrichment: Any,
) -> GapAnalysis:
    profile_skills = get_profile_skills(profile)

    required_skills = normalize_collection(enrichment.required_skills)

    preferred_skills = normalize_collection(enrichment.preferred_skills)

    platforms = normalize_collection(enrichment.cloud_platforms) | normalize_collection(
        enrichment.data_platforms
    )

    matched_required = required_skills & profile_skills

    missing_required = required_skills - profile_skills

    matched_preferred = preferred_skills & profile_skills

    missing_preferred = preferred_skills - profile_skills

    matched_platforms = platforms & profile_skills

    missing_platforms = platforms - profile_skills

    required_ratio = calculate_ratio(
        matched_required,
        required_skills,
    )

    preferred_ratio = calculate_ratio(
        matched_preferred,
        preferred_skills,
    )

    platform_ratio = calculate_ratio(
        matched_platforms,
        platforms,
    )

    profile_experience = get_profile_experience(profile)

    required_experience = enrichment.minimum_experience_years

    (
        experience_fit,
        experience_gap_years,
    ) = analyze_experience(
        required_years=(required_experience),
        profile_experience=(profile_experience),
    )

    deal_breakers = sorted(set(enrichment.deal_breakers or []))

    gap_score = calculate_gap_score(
        required_skills=(required_skills),
        required_ratio=(required_ratio),
        preferred_skills=(preferred_skills),
        preferred_ratio=(preferred_ratio),
        platforms=(platforms),
        platform_ratio=(platform_ratio),
        required_experience=(required_experience),
        experience_fit=(experience_fit),
        deal_breakers=(deal_breakers),
    )

    summary = build_fit_summary(
        required_skills=(required_skills),
        matched_required=(matched_required),
        missing_required=(missing_required),
        preferred_skills=(preferred_skills),
        matched_preferred=(matched_preferred),
        missing_preferred=(missing_preferred),
        platforms=(platforms),
        matched_platforms=(matched_platforms),
        missing_platforms=(missing_platforms),
        required_experience=(required_experience),
        experience_fit=(experience_fit),
        experience_gap_years=(experience_gap_years),
        deal_breakers=(deal_breakers),
        gap_score=(gap_score),
    )

    return GapAnalysis(
        matched_required_skills=sorted(matched_required),
        missing_required_skills=sorted(missing_required),
        matched_preferred_skills=sorted(matched_preferred),
        missing_preferred_skills=sorted(missing_preferred),
        matched_platforms=sorted(matched_platforms),
        missing_platforms=sorted(missing_platforms),
        deal_breakers=(deal_breakers),
        experience_fit=(experience_fit),
        experience_gap_years=(experience_gap_years),
        required_skill_match_ratio=(required_ratio),
        preferred_skill_match_ratio=(preferred_ratio),
        platform_match_ratio=(platform_ratio),
        gap_score=(gap_score),
        fit_summary=(summary),
    )
