from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from jobintel.application_ops.answer_bank import (
    build_answer_bank,
    serialize_answer_bank,
)
from jobintel.application_ops.readiness import (
    readiness_payload,
)
from jobintel.application_ops.service import (
    ApplicationOpsError,
    history,
    require_job,
    set_status,
    status_summary,
)
from jobintel.application_ops.status import (
    CANONICAL_STATUSES,
)
from jobintel.application_ops.workday_assist import (
    build_workday_suggestions,
)
from jobintel.db.session import SessionLocal
from jobintel.profile.runtime import (
    DEFAULT_PROFILE_NAME,
)
from jobintel.resume.service import (
    load_universal_profile,
)

router = APIRouter(
    prefix="/application-ops",
    tags=["Application Ops"],
)


class StatusUpdateRequest(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=50,
    )
    notes: str | None = None


def get_db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def json_safe(
    value: Any,
):
    if value is None:
        return None

    if isinstance(
        value,
        (
            date,
            datetime,
        ),
    ):
        return value.isoformat()

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    return str(value)


def serialize_record(
    record,
) -> dict:
    return {
        column.name: json_safe(
            getattr(
                record,
                column.name,
            )
        )
        for column in record.__table__.columns
    }


def get_profile():
    profile = load_universal_profile()

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=("Universal candidate profile is not available."),
        )

    return profile


@router.get("/summary")
def summary(
    session: Session = Depends(get_db),
):
    counts = status_summary(
        session=session,
        profile_name=DEFAULT_PROFILE_NAME,
    )

    return {
        "profile_name": DEFAULT_PROFILE_NAME,
        "counts": counts,
        "completed_outcomes": (
            counts.get(
                "interviewing",
                0,
            )
            + counts.get(
                "rejected",
                0,
            )
            + counts.get(
                "offer",
                0,
            )
        ),
        "allowed_statuses": sorted(CANONICAL_STATUSES),
    }


@router.get("/jobs/{job_id}/answers")
def answers(
    job_id: int,
    session: Session = Depends(get_db),
):
    profile = get_profile()

    try:
        job = require_job(
            session,
            job_id,
        )
    except ApplicationOpsError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    answer_bank = build_answer_bank(
        profile,
        company=job.company,
        title=job.title,
    )

    return {
        "job_id": job.id,
        "company": job.company,
        "title": job.title,
        "answers": serialize_answer_bank(answer_bank),
        "review_required": True,
    }


@router.get("/jobs/{job_id}/readiness")
def readiness(
    job_id: int,
    session: Session = Depends(get_db),
):
    profile = get_profile()

    try:
        job = require_job(
            session,
            job_id,
        )
    except ApplicationOpsError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "job_id": job.id,
        "company": job.company,
        "title": job.title,
        **readiness_payload(
            profile=profile,
            job=job,
        ),
    }


@router.get("/jobs/{job_id}/workday-assist")
def workday_assist(
    job_id: int,
    session: Session = Depends(get_db),
):
    profile = get_profile()

    try:
        job = require_job(
            session,
            job_id,
        )
    except ApplicationOpsError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    answer_bank = build_answer_bank(
        profile,
        company=job.company,
        title=job.title,
    )

    suggestions = build_workday_suggestions(answer_bank)

    return {
        "job_id": job.id,
        "apply_url": job.apply_url,
        "review_required": True,
        "auto_submit_allowed": False,
        "suggestions": [item.to_dict() for item in suggestions],
    }


@router.post("/jobs/{job_id}/status")
def update_status(
    job_id: int,
    payload: StatusUpdateRequest,
    session: Session = Depends(get_db),
):
    try:
        record = set_status(
            session=session,
            job_id=job_id,
            profile_name=(DEFAULT_PROFILE_NAME),
            status=payload.status,
            notes=payload.notes,
            source="application_ops_api",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except ApplicationOpsError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {"state": serialize_record(record)}


@router.get("/jobs/{job_id}/history")
def application_history(
    job_id: int,
    session: Session = Depends(get_db),
):
    try:
        records = history(
            session=session,
            job_id=job_id,
            profile_name=(DEFAULT_PROFILE_NAME),
        )
    except ApplicationOpsError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "job_id": job_id,
        "count": len(records),
        "history": [serialize_record(record) for record in records],
    }
