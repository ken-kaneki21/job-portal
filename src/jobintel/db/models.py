from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jobintel.db.base import Base


class JobRecord(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_identifier",
            "external_id",
            name="uq_job_source_external_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(String(500))

    department: Mapped[str | None] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(Text)

    apply_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    canonical_key: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class JobSourceRecord(Base):
    __tablename__ = "job_sources"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_identifier",
            "external_id",
            name="uq_job_source_identity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_url: Mapped[str | None] = mapped_column(Text)

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ScanRecord(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    jobs_fetched: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    error_type: Mapped[str | None] = mapped_column(String(255))

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class RawJobRecord(Base):
    __tablename__ = "raw_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class CompanyRecord(Base):
    __tablename__ = "companies"

    __table_args__ = (
        UniqueConstraint(
            "ats",
            "identifier",
            name="uq_company_ats_identifier",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ats: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    priority: Mapped[int] = mapped_column(
        nullable=False,
        default=100,
        server_default=text("100"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class JobRankingRecord(Base):
    __tablename__ = "job_rankings"

    id: Mapped[int] = mapped_column(primary_key=True)
    gap_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    profile_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    bucket: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    score: Mapped[float] = mapped_column(
        nullable=False,
    )

    deterministic_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    semantic_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    rank_position: Mapped[int] = mapped_column(
        nullable=False,
    )

    ranked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    pipeline_run_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "pipeline_runs.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )


class JobApplicationStateRecord(Base):
    __tablename__ = "job_application_states"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "profile_name",
            name="uq_job_application_state",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    profile_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new",
        server_default=text("'new'"),
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PipelineRunRecord(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    jobs_fetched: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    active_jobs: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    eligible_jobs: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    rankings_persisted: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    error_message: Mapped[str | None] = mapped_column(Text)


class NotificationRecord(Base):
    __tablename__ = "notifications"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "profile_name",
            "notification_type",
            name="uq_notification_job_profile_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    pipeline_run_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "pipeline_runs.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    profile_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    error_message: Mapped[str | None] = mapped_column(Text)


class CompanyDiscoveryCandidateRecord(Base):
    __tablename__ = "company_discovery_candidates"

    __table_args__ = (
        UniqueConstraint(
            "normalized_name",
            name=("uq_company_discovery_normalized_name"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )

    discovered_ats: Mapped[str | None] = mapped_column(String(50))

    discovered_identifier: Mapped[str | None] = mapped_column(String(255))

    career_url: Mapped[str | None] = mapped_column(Text)

    attempt_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    error_message: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class JobEmbeddingRecord(Base):
    __tablename__ = "job_embeddings"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "model_name",
            name=("uq_job_embedding_job_model"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class JobEnrichmentRecord(Base):
    __tablename__ = "job_enrichments"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            name="uq_job_enrichment_job_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    extractor_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    minimum_experience_years: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    maximum_experience_years: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    seniority: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    education: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    required_skills: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    preferred_skills: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    cloud_platforms: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    data_platforms: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    responsibilities: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    deal_breakers: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    extracted_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class JobGapAnalysisRecord(Base):
    __tablename__ = "job_gap_analyses"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "profile_name",
            name="uq_job_gap_analysis_job_profile",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    profile_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    analyzer_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    matched_required_skills: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    missing_required_skills: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    matched_preferred_skills: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    missing_preferred_skills: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    matched_platforms: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    missing_platforms: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    deal_breakers: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    experience_fit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unknown",
        server_default=text("'unknown'"),
        index=True,
    )

    experience_gap_years: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    required_skill_match_ratio: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
        server_default=text("0"),
    )

    preferred_skill_match_ratio: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
        server_default=text("0"),
    )

    platform_match_ratio: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
        server_default=text("0"),
    )

    gap_score: Mapped[float] = mapped_column(
        nullable=False,
        index=True,
    )

    fit_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    analysis_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class JobApplicationAssetRecord(Base):
    __tablename__ = "job_application_assets"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "profile_name",
            name="uq_job_application_asset_job_profile",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    profile_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    generator_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    recruiter_dm: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    email_subject: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    email_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    cover_note: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    resume_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    skills_to_emphasize: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    missing_skills_warning: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    resume_bullets_to_emphasize: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    interview_talking_points: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    generated_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
