from __future__ import annotations

from dataclasses import dataclass

from jobintel.db.models import JobRecord
from jobintel.profile.universal import UniversalCandidateProfile
from jobintel.ranking.scoring import (
    contains_skill,
    detect_min_experience,
    normalize_text,
    phrase_in_text,
)


@dataclass(frozen=True)
class ProfileEvidenceScore:
    score: float
    reasons: tuple[str, ...]


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            continue

        lowered = cleaned.lower()
        if lowered in seen:
            continue

        seen.add(lowered)
        output.append(cleaned)

    return output


def profile_evidence_skills(
    profile: UniversalCandidateProfile,
) -> list[str]:
    values = (
        profile.core_skills
        + profile.secondary_skills
        + profile.tools
        + profile.cloud_platforms
    )

    for experience in profile.experience:
        values.extend(experience.skills)

    for project in profile.projects:
        values.extend(project.skills)

    return unique_strings(values)


def score_experience_fit(
    job_text: str,
    profile: UniversalCandidateProfile,
) -> tuple[float, str]:
    required = detect_min_experience(job_text)
    actual = profile.total_experience_years

    if actual is None:
        return 0.5, "Structured candidate experience unavailable"

    if required is None:
        return 1.5, f"Candidate experience evidence: {actual:.1f} years"

    difference = required - actual

    if difference <= 0.5:
        return (
            3.5,
            f"Experience evidence fits requirement: {actual:.1f} years vs {required}+",
        )

    if difference <= 2.0:
        return (
            2.0,
            f"Experience evidence is a reasonable stretch: {actual:.1f} years vs {required}+",
        )

    return (
        0.5,
        f"Experience evidence below stated requirement: {actual:.1f} years vs {required}+",
    )


def score_role_family(
    job: JobRecord,
    profile: UniversalCandidateProfile,
) -> tuple[float, str | None]:
    title = normalize_text(job.title)

    for role in profile.role_families:
        if not role.enabled:
            continue

        role_name = normalize_text(role.name)

        if phrase_in_text(role_name, title):
            return 1.5, "Structured role-family evidence: " + role.name

        significant_words = [word for word in role_name.split() if len(word) >= 4]

        if significant_words and all(word in title for word in significant_words):
            return 1.25, "Structured role-family evidence: " + role.name

    return 0.0, None


def score_profile_evidence(
    job: JobRecord,
    profile: UniversalCandidateProfile,
) -> ProfileEvidenceScore:
    job_text = normalize_text(
        " ".join(
            [
                job.title or "",
                job.description or "",
                job.department or "",
            ]
        )
    )

    reasons: list[str] = []

    experience_score, experience_reason = score_experience_fit(
        job_text,
        profile,
    )
    reasons.append(experience_reason)

    skills = profile_evidence_skills(profile)

    matched = [skill for skill in skills if contains_skill(job_text, skill.lower())]

    skill_score = min(4.0, len(matched) * 0.8)

    if matched:
        reasons.append("Resume evidence skills: " + ", ".join(matched[:6]))

    role_score, role_reason = score_role_family(
        job,
        profile,
    )

    if role_reason:
        reasons.append(role_reason)

    industry_matches = [
        industry
        for industry in profile.industries
        if phrase_in_text(industry, job_text)
    ]

    industry_score = min(
        1.0,
        len(industry_matches) * 0.5,
    )

    if industry_matches:
        reasons.append("Industry evidence: " + ", ".join(industry_matches[:3]))

    score = min(
        10.0,
        experience_score + skill_score + role_score + industry_score,
    )

    return ProfileEvidenceScore(
        score=round(score, 2),
        reasons=tuple(reasons),
    )
