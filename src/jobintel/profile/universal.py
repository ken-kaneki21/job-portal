from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

RolePriority = Literal[
    "primary",
    "secondary",
    "discovery",
    "disabled",
]


class RoleFamily(BaseModel):
    name: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    priority: RolePriority = "discovery"
    enabled: bool = True
    matched_signals: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    skills: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class ProjectEntry(BaseModel):
    name: str
    description: str | None = None
    skills: list[str] = Field(default_factory=list)


class CandidatePreferences(BaseModel):
    preferred_locations: list[str] = Field(default_factory=list)
    allowed_countries: list[str] = Field(default_factory=list)

    blocked_location_terms: list[str] = Field(default_factory=list)
    blocked_titles: list[str] = Field(default_factory=list)

    remote_preference: bool | None = None
    hybrid_preference: bool | None = None
    relocation_allowed: bool | None = None

    notice_period_days: int | None = None
    expected_compensation: str | None = None


class CandidateIdentity(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None

    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None


class UniversalCandidateProfile(BaseModel):
    schema_version: str = "2.0"

    profile_name: str = "default"

    identity: CandidateIdentity = Field(
        default_factory=CandidateIdentity,
    )

    headline: str | None = None
    summary: str | None = None

    total_experience_years: float | None = None

    role_families: list[RoleFamily] = Field(
        default_factory=list,
    )

    core_skills: list[str] = Field(
        default_factory=list,
    )

    secondary_skills: list[str] = Field(
        default_factory=list,
    )

    tools: list[str] = Field(
        default_factory=list,
    )

    cloud_platforms: list[str] = Field(
        default_factory=list,
    )

    industries: list[str] = Field(
        default_factory=list,
    )

    certifications: list[str] = Field(
        default_factory=list,
    )

    experience: list[ExperienceEntry] = Field(
        default_factory=list,
    )

    education: list[EducationEntry] = Field(
        default_factory=list,
    )

    projects: list[ProjectEntry] = Field(
        default_factory=list,
    )

    preferences: CandidatePreferences = Field(
        default_factory=CandidatePreferences,
    )

    source_resume_filename: str | None = None
    source_resume_sha256: str | None = None

    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
