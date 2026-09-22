from __future__ import annotations

from datetime import UTC, datetime

from jobintel.db.models import JobRecord
from jobintel.profile.universal import (
    ExperienceEntry,
    ProjectEntry,
    RoleFamily,
    UniversalCandidateProfile,
)
from jobintel.ranking.profile_evidence import (
    score_profile_evidence,
)


def make_job(
    *,
    title: str,
    description: str,
) -> JobRecord:
    return JobRecord(
        id=1,
        source="linkedin",
        source_identifier="linkedin",
        external_id="abc",
        company="Example",
        title=title,
        location="Bangalore",
        department="Data",
        description=description,
        apply_url="https://example.com/job",
        fingerprint="a" * 64,
        canonical_key=None,
        is_active=True,
        closed_at=None,
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )


def test_profile_evidence_rewards_resume_backed_fit():
    profile = UniversalCandidateProfile(
        profile_name="universal",
        total_experience_years=2.2,
        role_families=[
            RoleFamily(
                name="Data Engineer",
                confidence=1.0,
                priority="primary",
            )
        ],
        core_skills=[
            "Python",
            "SQL",
            "Snowflake",
        ],
        industries=["Healthcare"],
        experience=[
            ExperienceEntry(
                title="Data Engineer",
                description="Built Snowflake pipelines.",
                skills=["Python", "Snowflake"],
            )
        ],
        projects=[
            ProjectEntry(
                name="Pipeline Toolkit",
                skills=["SQL"],
            )
        ],
    )

    job = make_job(
        title="Data Engineer",
        description=(
            "2+ years experience with Python, SQL and Snowflake in Healthcare."
        ),
    )

    result = score_profile_evidence(job, profile)

    assert result.score >= 7.0
    assert any("Resume evidence skills" in reason for reason in result.reasons)


def test_profile_evidence_handles_unclear_experience():
    profile = UniversalCandidateProfile(
        profile_name="universal",
        total_experience_years=2.2,
    )

    job = make_job(
        title="Data Engineer",
        description="Build data pipelines.",
    )

    result = score_profile_evidence(job, profile)

    assert result.score >= 1.0
