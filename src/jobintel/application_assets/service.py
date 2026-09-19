import hashlib
import json

from sqlalchemy import select

from jobintel.application_assets.generator import (
    GENERATOR_VERSION,
    generate_application_assets,
)
from jobintel.db.models import (
    JobApplicationAssetRecord,
    JobEnrichmentRecord,
    JobGapAnalysisRecord,
    JobRankingRecord,
    JobRecord,
)
from jobintel.profile.loader import load_profile


PROFILE_PATH = "profiles/data_engineer.json"


class AssetGenerationError(Exception):
    pass


def build_content_hash(
    *,
    job: JobRecord,
    enrichment: JobEnrichmentRecord,
    gap: JobGapAnalysisRecord,
    ranking: JobRankingRecord,
) -> str:
    payload = {
        "generator_version": GENERATOR_VERSION,
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company,
        "enrichment_hash": enrichment.content_hash,
        "gap_hash": gap.content_hash,
        "ranking_score": ranking.score,
        "bucket": ranking.bucket,
    }

    raw = json.dumps(
        payload,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def load_latest_ranking(
    *,
    session,
    job_id: int,
    profile_name: str,
) -> JobRankingRecord | None:
    return session.scalar(
        select(
            JobRankingRecord
        )
        .where(
            JobRankingRecord.job_id
            == job_id
        )
        .where(
            JobRankingRecord.profile_name
            == profile_name
        )
        .order_by(
            JobRankingRecord.ranked_at.desc(),
            JobRankingRecord.id.desc(),
        )
        .limit(1)
    )


def regenerate_application_assets_for_job(
    *,
    session,
    job_id: int,
    profile_name: str = "data_engineer",
) -> JobApplicationAssetRecord:
    profile = load_profile(
        PROFILE_PATH
    )

    if profile.name != profile_name:
        raise AssetGenerationError(
            f"Profile '{profile_name}' is not configured."
        )

    job = session.get(
        JobRecord,
        job_id,
    )

    if job is None:
        raise AssetGenerationError(
            f"Job {job_id} was not found."
        )

    enrichment = session.scalar(
        select(
            JobEnrichmentRecord
        )
        .where(
            JobEnrichmentRecord.job_id
            == job_id
        )
        .limit(1)
    )

    if enrichment is None:
        raise AssetGenerationError(
            f"Job {job_id} has no enrichment record."
        )

    gap = session.scalar(
        select(
            JobGapAnalysisRecord
        )
        .where(
            JobGapAnalysisRecord.job_id
            == job_id
        )
        .where(
            JobGapAnalysisRecord.profile_name
            == profile_name
        )
        .limit(1)
    )

    if gap is None:
        raise AssetGenerationError(
            f"Job {job_id} has no gap analysis "
            f"for profile '{profile_name}'."
        )

    ranking = load_latest_ranking(
        session=session,
        job_id=job_id,
        profile_name=profile_name,
    )

    if ranking is None:
        raise AssetGenerationError(
            f"Job {job_id} has no ranking "
            f"for profile '{profile_name}'."
        )

    assets = generate_application_assets(
        profile=profile,
        job=job,
        enrichment=enrichment,
        gap=gap,
        ranking=ranking,
    )

    content_hash = build_content_hash(
        job=job,
        enrichment=enrichment,
        gap=gap,
        ranking=ranking,
    )

    payload = assets.to_dict()

    existing = session.scalar(
        select(
            JobApplicationAssetRecord
        )
        .where(
            JobApplicationAssetRecord.job_id
            == job_id
        )
        .where(
            JobApplicationAssetRecord.profile_name
            == profile_name
        )
        .limit(1)
    )

    if existing is None:
        existing = JobApplicationAssetRecord(
            job_id=job_id,
            profile_name=profile_name,
            generator_version=(
                GENERATOR_VERSION
            ),
            content_hash=content_hash,
            recruiter_dm=(
                assets.recruiter_dm
            ),
            email_subject=(
                assets.email_subject
            ),
            email_body=(
                assets.email_body
            ),
            cover_note=(
                assets.cover_note
            ),
            resume_summary=(
                assets.resume_summary
            ),
            skills_to_emphasize=(
                assets.skills_to_emphasize
            ),
            missing_skills_warning=(
                assets.missing_skills_warning
            ),
            resume_bullets_to_emphasize=(
                assets.resume_bullets_to_emphasize
            ),
            interview_talking_points=(
                assets.interview_talking_points
            ),
            generated_payload=payload,
        )

        session.add(
            existing
        )

    else:
        existing.generator_version = (
            GENERATOR_VERSION
        )

        existing.content_hash = (
            content_hash
        )

        existing.recruiter_dm = (
            assets.recruiter_dm
        )

        existing.email_subject = (
            assets.email_subject
        )

        existing.email_body = (
            assets.email_body
        )

        existing.cover_note = (
            assets.cover_note
        )

        existing.resume_summary = (
            assets.resume_summary
        )

        existing.skills_to_emphasize = (
            assets.skills_to_emphasize
        )

        existing.missing_skills_warning = (
            assets.missing_skills_warning
        )

        existing.resume_bullets_to_emphasize = (
            assets.resume_bullets_to_emphasize
        )

        existing.interview_talking_points = (
            assets.interview_talking_points
        )

        existing.generated_payload = (
            payload
        )

    session.commit()
    session.refresh(
        existing
    )

    return existing