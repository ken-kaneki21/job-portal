import re
from dataclasses import dataclass
from datetime import datetime, timezone

from jobintel.db.models import (
    JobRecord,
    JobSourceRecord,
)
from jobintel.profile.models import (
    CandidateProfile,
)


SKILL_ALIASES: dict[
    str,
    tuple[str, ...],
] = {
    "python": (
        "python",
    ),
    "sql": (
        "sql",
    ),
    "snowflake": (
        "snowflake",
    ),
    "dbt": (
        "dbt",
        "data build tool",
    ),
    "airflow": (
        "airflow",
        "apache airflow",
    ),
    "azure data factory": (
        "azure data factory",
        "adf",
    ),
    "pyspark": (
        "pyspark",
        "py spark",
    ),
    "spark": (
        "apache spark",
        "spark",
    ),
    "databricks": (
        "databricks",
    ),
    "aws": (
        "aws",
        "amazon web services",
    ),
    "azure": (
        "azure",
        "microsoft azure",
    ),
    "postgresql": (
        "postgresql",
        "postgres",
    ),
    "etl": (
        "etl",
        "extract transform load",
    ),
    "elt": (
        "elt",
    ),
    "data modeling": (
        "data modeling",
        "data modelling",
    ),
    "power bi": (
        "power bi",
        "powerbi",
    ),
    "docker": (
        "docker",
    ),
    "git": (
        "git",
        "github",
        "gitlab",
    ),
}


DIRECT_SOURCES = {
    "greenhouse",
    "lever",
    "ashby",
    "smartrecruiters",
}


@dataclass(frozen=True)
class RankedJob:
    job: JobRecord

    eligible: bool
    rejection_reasons: tuple[str, ...]

    # Final blended score used for ranking.
    score: float

    # Original deterministic score before
    # semantic blending.
    deterministic_score: float

    title_score: float
    location_score: float
    skill_score: float
    experience_score: float
    freshness_score: float
    source_score: float

    # 0..10 semantic contribution.
    semantic_score: float

    # 0..100 structured profile-vs-JD gap fit.
    gap_score: float

    matched_core_skills: tuple[str, ...]
    matched_secondary_skills: tuple[str, ...]

    detected_experience: int | None

    sources: tuple[str, ...]

    preferred_apply_url: str

    reasons: tuple[str, ...]


def normalize_text(
    value: str | None,
) -> str:
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        value.lower(),
    ).strip()


def phrase_in_text(
    phrase: str,
    text: str,
) -> bool:
    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(
            phrase.lower()
        )
        + r"(?![a-z0-9])"
    )

    return bool(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
    )


def contains_skill(
    text: str,
    skill: str,
) -> bool:
    aliases = SKILL_ALIASES.get(
        skill,
        (skill,),
    )

    return any(
        phrase_in_text(
            alias,
            text,
        )
        for alias in aliases
    )


def detect_min_experience(
    text: str,
) -> int | None:
    patterns = [
        (
            r"(\d+)\s*(?:-|–|to)\s*"
            r"\d+\s*(?:years|yrs)"
        ),
        (
            r"minimum\s+(?:of\s+)?"
            r"(\d+)\s*(?:years|yrs)"
        ),
        (
            r"at\s+least\s+"
            r"(\d+)\s*(?:years|yrs)"
        ),
        (
            r"(\d+)\+\s*"
            r"(?:years|yrs)"
        ),
        (
            r"(\d+)\s*(?:years|yrs)"
            r"\s+of\s+experience"
        ),
    ]

    values: list[int] = []

    for pattern in patterns:
        values.extend(
            int(value)
            for value in re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    return (
        min(values)
        if values
        else None
    )


def check_title_eligibility(
    title: str,
    profile: CandidateProfile,
) -> tuple[
    bool,
    list[str],
]:
    normalized = normalize_text(
        title
    )

    rejection_reasons: list[str] = []

    for excluded in (
        profile.exclude_titles
    ):
        if phrase_in_text(
            excluded,
            normalized,
        ):
            rejection_reasons.append(
                f"Excluded title: "
                f"{excluded}"
            )

    if rejection_reasons:
        return (
            False,
            rejection_reasons,
        )

    target_match = any(
        phrase_in_text(
            target,
            normalized,
        )
        for target
        in profile.target_titles
    )

    adjacent_match = any(
        phrase_in_text(
            adjacent,
            normalized,
        )
        for adjacent
        in profile.adjacent_titles
    )

    if (
        not target_match
        and not adjacent_match
    ):
        return (
            False,
            [
                "Outside target role family"
            ],
        )

    return (
        True,
        [],
    )


def check_location_eligibility(
    location: str | None,
    profile: CandidateProfile,
) -> tuple[
    bool,
    list[str],
]:
    normalized = normalize_text(
        location
    )

    if not normalized:
        return (
            True,
            [],
        )

    for blocked in (
        profile.blocked_location_terms
    ):
        if blocked in normalized:
            return (
                False,
                [
                    "Location restriction: "
                    f"{location}"
                ],
            )

    if any(
        preferred in normalized
        for preferred
        in profile.preferred_locations
    ):
        return (
            True,
            [],
        )

    if any(
        country in normalized
        for country
        in profile.allowed_countries
    ):
        return (
            True,
            [],
        )

    if normalized == "remote":
        return (
            True,
            [],
        )

    return (
        False,
        [
            "Outside preferred geography: "
            f"{location}"
        ],
    )


def score_title(
    title: str,
    profile: CandidateProfile,
) -> tuple[
    float,
    list[str],
]:
    normalized = normalize_text(
        title
    )

    for target in (
        profile.target_titles
    ):
        if phrase_in_text(
            target,
            normalized,
        ):
            return (
                35.0,
                [
                    "Strong target-role "
                    "title match"
                ],
            )

    for adjacent in (
        profile.adjacent_titles
    ):
        if phrase_in_text(
            adjacent,
            normalized,
        ):
            return (
                22.0,
                [
                    "Adjacent-role "
                    "title match"
                ],
            )

    return (
        0.0,
        [],
    )


def score_location(
    location: str | None,
    profile: CandidateProfile,
) -> tuple[
    float,
    list[str],
]:
    normalized = normalize_text(
        location
    )

    if not normalized:
        return (
            8.0,
            [
                "Location unspecified"
            ],
        )

    for preferred in (
        profile.preferred_locations
    ):
        if preferred in normalized:
            return (
                20.0,
                [
                    "Preferred location: "
                    f"{location}"
                ],
            )

    if normalized == "remote":
        return (
            18.0,
            [
                "Remote role"
            ],
        )

    if any(
        country in normalized
        for country
        in profile.allowed_countries
    ):
        return (
            15.0,
            [
                "Allowed country: "
                f"{location}"
            ],
        )

    return (
        0.0,
        [],
    )


def score_skills(
    text: str,
    profile: CandidateProfile,
) -> tuple[
    float,
    tuple[str, ...],
    tuple[str, ...],
]:
    matched_core = tuple(
        skill
        for skill
        in profile.core_skills
        if contains_skill(
            text,
            skill,
        )
    )

    matched_secondary = tuple(
        skill
        for skill
        in profile.secondary_skills
        if contains_skill(
            text,
            skill,
        )
    )

    core_ratio = (
        len(
            matched_core
        )
        / len(
            profile.core_skills
        )
        if profile.core_skills
        else 0.0
    )

    secondary_ratio = (
        len(
            matched_secondary
        )
        / len(
            profile.secondary_skills
        )
        if profile.secondary_skills
        else 0.0
    )

    score = (
        core_ratio * 15.0
        + secondary_ratio * 5.0
    )

    return (
        min(
            score,
            20.0,
        ),
        matched_core,
        matched_secondary,
    )


def score_experience(
    description: str,
    profile: CandidateProfile,
) -> tuple[
    float,
    int | None,
    list[str],
]:
    required = detect_min_experience(
        description
    )

    if required is None:
        return (
            1.0,
            None,
            [
                "Experience requirement unclear"
            ],
        )

    if (
        required
        <= profile
        .max_preferred_experience_years
    ):
        return (
            10.0,
            required,
            [
                "Experience requirement: "
                f"{required}+ years"
            ],
        )

    if (
        required
        <= profile
        .hard_max_experience_years
    ):
        return (
            4.0,
            required,
            [
                "Stretch experience "
                "requirement: "
                f"{required}+ years"
            ],
        )

    return (
        0.0,
        required,
        [
            "Experience requirement "
            "too high: "
            f"{required}+ years"
        ],
    )


def score_freshness(
    first_seen_at: datetime,
) -> float:
    now = datetime.now(
        timezone.utc
    )

    age_days = (
        now
        - first_seen_at
    ).total_seconds() / 86400

    if age_days <= 1:
        return 5.0

    if age_days <= 3:
        return 4.0

    if age_days <= 7:
        return 3.0

    if age_days <= 14:
        return 2.0

    return 1.0


def score_source_quality(
    sources: list[
        JobSourceRecord
    ],
) -> tuple[
    float,
    tuple[str, ...],
    str,
    list[str],
]:
    source_names = tuple(
        sorted(
            {
                source.source
                for source
                in sources
            }
        )
    )

    direct_sources = [
        source
        for source
        in sources
        if (
            source.source
            in DIRECT_SOURCES
        )
    ]

    aggregator_sources = [
        source
        for source
        in sources
        if (
            source.source
            == "adzuna"
        )
    ]

    if direct_sources:
        preferred_source = next(
            (
                source
                for source
                in direct_sources
                if (
                    source.is_primary
                    and source.source_url
                )
            ),
            None,
        )

        if preferred_source is None:
            preferred_source = next(
                (
                    source
                    for source
                    in direct_sources
                    if source.source_url
                ),
                None,
            )

        preferred_url = (
            preferred_source.source_url
            if preferred_source
            is not None
            else ""
        )

        if aggregator_sources:
            return (
                10.0,
                source_names,
                preferred_url,
                [
                    "Direct ATS posting "
                    "confirmed by "
                    "additional source"
                ],
            )

        return (
            8.0,
            source_names,
            preferred_url,
            [
                "Direct employer ATS source"
            ],
        )

    if aggregator_sources:
        preferred_source = next(
            (
                source
                for source
                in aggregator_sources
                if source.source_url
            ),
            None,
        )

        preferred_url = (
            preferred_source.source_url
            if preferred_source
            is not None
            else ""
        )

        return (
            2.0,
            source_names,
            preferred_url,
            [
                "Aggregator discovery source"
            ],
        )

    preferred_source = next(
        (
            source
            for source
            in sources
            if source.source_url
        ),
        None,
    )

    preferred_url = (
        preferred_source.source_url
        if preferred_source
        is not None
        else ""
    )

    return (
        0.0,
        source_names,
        preferred_url,
        [
            "Unclassified source"
        ],
    )


def rank_job(
    job: JobRecord,
    profile: CandidateProfile,
    sources: list[
        JobSourceRecord
    ] | None = None,
) -> RankedJob:
    sources = sources or []

    rejection_reasons: list[str] = []

    (
        title_eligible,
        title_rejections,
    ) = check_title_eligibility(
        job.title,
        profile,
    )

    rejection_reasons.extend(
        title_rejections
    )

    (
        location_eligible,
        location_rejections,
    ) = check_location_eligibility(
        job.location,
        profile,
    )

    rejection_reasons.extend(
        location_rejections
    )

    combined_text = normalize_text(
        " ".join(
            [
                job.title or "",
                job.description or "",
                job.department or "",
            ]
        )
    )

    detected_experience = (
        detect_min_experience(
            combined_text
        )
    )

    if (
        detected_experience
        is not None
        and detected_experience
        > profile
        .hard_max_experience_years
    ):
        rejection_reasons.append(
            "Experience above hard "
            "maximum: "
            f"{detected_experience}+ years"
        )

    eligible = (
        title_eligible
        and location_eligible
        and not rejection_reasons
    )

    (
        source_score,
        source_names,
        preferred_apply_url,
        source_reasons,
    ) = score_source_quality(
        sources
    )

    if not preferred_apply_url:
        preferred_apply_url = (
            job.apply_url
        )

    if not eligible:
        return RankedJob(
            job=job,
            eligible=False,
            rejection_reasons=tuple(
                rejection_reasons
            ),
            score=0.0,
            deterministic_score=0.0,
            title_score=0.0,
            location_score=0.0,
            skill_score=0.0,
            experience_score=0.0,
            freshness_score=0.0,
            source_score=0.0,
            semantic_score=0.0,
            gap_score=50.0,
            matched_core_skills=(),
            matched_secondary_skills=(),
            detected_experience=(
                detected_experience
            ),
            sources=source_names,
            preferred_apply_url=(
                preferred_apply_url
            ),
            reasons=(),
        )

    (
        title_score,
        title_reasons,
    ) = score_title(
        job.title,
        profile,
    )

    (
        location_score,
        location_reasons,
    ) = score_location(
        job.location,
        profile,
    )

    (
        skill_score,
        matched_core,
        matched_secondary,
    ) = score_skills(
        combined_text,
        profile,
    )

    (
        experience_score,
        detected_experience,
        experience_reasons,
    ) = score_experience(
        combined_text,
        profile,
    )

    freshness_score = (
        score_freshness(
            job.first_seen_at
        )
    )

    deterministic_score = round(
        min(
            (
                title_score
                + location_score
                + skill_score
                + experience_score
                + freshness_score
                + source_score
            ),
            100.0,
        ),
        2,
    )

    reasons = (
        title_reasons
        + location_reasons
        + experience_reasons
        + source_reasons
    )

    if matched_core:
        reasons.append(
            "Core skills: "
            + ", ".join(
                matched_core
            )
        )

    if matched_secondary:
        reasons.append(
            "Secondary skills: "
            + ", ".join(
                matched_secondary
            )
        )

    return RankedJob(
        job=job,
        eligible=True,
        rejection_reasons=(),
        score=deterministic_score,
        deterministic_score=(
            deterministic_score
        ),
        title_score=(
            title_score
        ),
        location_score=(
            location_score
        ),
        skill_score=round(
            skill_score,
            2,
        ),
        experience_score=(
            experience_score
        ),
        freshness_score=(
            freshness_score
        ),
        source_score=(
            source_score
        ),
        semantic_score=0.0,
        gap_score=50.0,
        matched_core_skills=(
            matched_core
        ),
        matched_secondary_skills=(
            matched_secondary
        ),
        detected_experience=(
            detected_experience
        ),
        sources=source_names,
        preferred_apply_url=(
            preferred_apply_url
        ),
        reasons=tuple(
            reasons
        ),
    )