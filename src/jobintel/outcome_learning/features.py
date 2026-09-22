from __future__ import annotations

import re
from dataclasses import dataclass

from jobintel.profile.models import CandidateProfile
from jobintel.ranking.scoring import (
    contains_skill,
    detect_min_experience,
    normalize_text,
)


@dataclass(frozen=True)
class OutcomeFeatures:
    source: str
    title_family: str
    location_family: str
    experience_band: str
    skill_signature: str
    deterministic_band: str
    semantic_band: str
    gap_band: str

    def items(self) -> tuple[tuple[str, str], ...]:
        return (
            ("source", self.source),
            ("title_family", self.title_family),
            ("location_family", self.location_family),
            ("experience_band", self.experience_band),
            ("skill_signature", self.skill_signature),
            ("deterministic_band", self.deterministic_band),
            ("semantic_band", self.semantic_band),
            ("gap_band", self.gap_band),
        )


def bucket_score(value: float | None, *, width: int = 10) -> str:
    if value is None:
        return "unknown"
    bounded = max(0.0, min(100.0, float(value)))
    lower = int(bounded // width) * width
    if lower >= 100:
        lower = 90
    return f"{lower}-{lower + width}"


def semantic_band(value: float | None) -> str:
    if value is None:
        return "unknown"
    bounded = max(0.0, min(10.0, float(value)))
    if bounded < 3:
        return "0-3"
    if bounded < 6:
        return "3-6"
    if bounded < 8:
        return "6-8"
    return "8-10"


def title_family(title: str | None) -> str:
    normalized = normalize_text(title)
    mappings = (
        ("data_engineering", ("data engineer", "data engineering", "etl engineer")),
        ("analytics_engineering", ("analytics engineer", "analytical engineer")),
        (
            "data_analytics",
            ("data analyst", "business data analyst", "analytics analyst"),
        ),
        ("ai_genai", ("ai engineer", "genai", "generative ai", "llm engineer")),
        ("machine_learning", ("machine learning", "ml engineer")),
        ("data_platform", ("data platform", "platform engineer")),
    )
    for family, phrases in mappings:
        if any(phrase in normalized for phrase in phrases):
            return family

    words = [word for word in re.findall(r"[a-z0-9]+", normalized) if len(word) >= 4]
    return "_".join(words[:3]) if words else "unknown"


def location_family(location: str | None) -> str:
    normalized = normalize_text(location)
    if not normalized:
        return "unknown"
    if "remote" in normalized:
        return "remote"
    if "bengaluru" in normalized or "bangalore" in normalized:
        return "bengaluru"
    if "hyderabad" in normalized:
        return "hyderabad"
    if "india" in normalized:
        return "india_other"
    cleaned = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return cleaned[:60] or "unknown"


def experience_band(description: str | None) -> str:
    years = detect_min_experience(normalize_text(description))
    if years is None:
        return "unknown"
    if years <= 2:
        return "0-2"
    if years <= 4:
        return "3-4"
    if years <= 6:
        return "5-6"
    if years <= 9:
        return "7-9"
    return "10+"


def skill_signature(*, text: str, profile: CandidateProfile) -> str:
    skills = list(profile.core_skills) + list(profile.secondary_skills)
    matched = [
        skill.strip().lower()
        for skill in skills
        if skill.strip() and contains_skill(text, skill)
    ]
    unique = sorted(set(matched))
    return "+".join(unique[:3]) if unique else "none"


def extract_outcome_features(
    *, job, ranking, profile: CandidateProfile
) -> OutcomeFeatures:
    combined_text = normalize_text(
        " ".join(
            [
                getattr(job, "title", "") or "",
                getattr(job, "description", "") or "",
                getattr(job, "department", "") or "",
            ]
        )
    )

    return OutcomeFeatures(
        source=str(getattr(job, "source", "") or "unknown").strip().lower(),
        title_family=title_family(getattr(job, "title", None)),
        location_family=location_family(getattr(job, "location", None)),
        experience_band=experience_band(getattr(job, "description", None)),
        skill_signature=skill_signature(text=combined_text, profile=profile),
        deterministic_band=bucket_score(getattr(ranking, "deterministic_score", None)),
        semantic_band=semantic_band(getattr(ranking, "semantic_score", None)),
        gap_band=bucket_score(getattr(ranking, "gap_score", None)),
    )
