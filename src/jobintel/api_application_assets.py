from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from jobintel.application_assets.service import (
    AssetGenerationError,
    regenerate_application_assets_for_job,
)
from jobintel.db.session import (
    SessionLocal,
)
from jobintel.profile.runtime import ACTIVE_PROFILE_NAME

router = APIRouter(tags=["Application Assets"])


def get_db():
    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()


def serialize_asset(
    record,
) -> dict:
    return {
        "id": record.id,
        "job_id": record.job_id,
        "profile_name": (record.profile_name),
        "generator_version": (record.generator_version),
        "content_hash": (record.content_hash),
        "recruiter_dm": (record.recruiter_dm),
        "email_subject": (record.email_subject),
        "email_body": (record.email_body),
        "cover_note": (record.cover_note),
        "resume_summary": (record.resume_summary),
        "skills_to_emphasize": (record.skills_to_emphasize),
        "missing_skills_warning": (record.missing_skills_warning),
        "resume_bullets_to_emphasize": (record.resume_bullets_to_emphasize),
        "interview_talking_points": (record.interview_talking_points),
        "generated_payload": (record.generated_payload),
        "created_at": (record.created_at.isoformat() if record.created_at else None),
        "updated_at": (record.updated_at.isoformat() if record.updated_at else None),
    }


@router.post("/jobs/{job_id}/regenerate-assets")
def regenerate_assets(
    job_id: int,
    profile_name: str = ACTIVE_PROFILE_NAME,
    session: Session = Depends(get_db),
):
    try:
        record = regenerate_application_assets_for_job(
            session=session,
            job_id=job_id,
            profile_name=profile_name,
        )

    except AssetGenerationError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        session.rollback()

        raise HTTPException(
            status_code=500,
            detail=(f"Asset regeneration failed: {exc}"),
        ) from exc

    return {
        "message": ("Application assets regenerated"),
        "application_assets": (serialize_asset(record)),
    }
