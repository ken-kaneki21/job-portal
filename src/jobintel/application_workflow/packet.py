from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import select

from jobintel.application_workflow.answers import build_application_answers
from jobintel.db.models import JobApplicationAssetRecord, JobRecord
from jobintel.profile.universal import UniversalCandidateProfile


class ApplicationPacketError(ValueError):
    pass


@dataclass(frozen=True)
class ApplicationPacket:
    job_id: int
    company: str
    title: str
    location: str | None
    apply_url: str
    profile_name: str
    answers: dict
    cover_note: str | None
    resume_summary: str | None
    skills_to_emphasize: list[str]
    missing_skills_warning: list[str]
    review_required: bool = True
    auto_submit_allowed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def build_application_packet(
    *,
    session,
    job_id: int,
    profile: UniversalCandidateProfile,
) -> ApplicationPacket:
    job = session.get(JobRecord, job_id)
    if job is None:
        raise ApplicationPacketError(f"Job {job_id} was not found.")

    asset = session.scalar(
        select(JobApplicationAssetRecord)
        .where(JobApplicationAssetRecord.job_id == job_id)
        .where(JobApplicationAssetRecord.profile_name == profile.profile_name)
        .limit(1)
    )

    answers = build_application_answers(profile)

    return ApplicationPacket(
        job_id=job.id,
        company=job.company,
        title=job.title,
        location=job.location,
        apply_url=str(job.apply_url),
        profile_name=profile.profile_name,
        answers=answers.to_dict(),
        cover_note=asset.cover_note if asset is not None else None,
        resume_summary=(asset.resume_summary if asset is not None else profile.summary),
        skills_to_emphasize=(
            list(asset.skills_to_emphasize or [])
            if asset is not None
            else (profile.core_skills + profile.secondary_skills)[:10]
        ),
        missing_skills_warning=(
            list(asset.missing_skills_warning or []) if asset is not None else []
        ),
    )
