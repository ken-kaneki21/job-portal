from __future__ import annotations

import hashlib
import hmac
import os
from urllib.parse import urlparse

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, HttpUrl

from jobintel.application_workflow.answers import build_application_answers
from jobintel.db.broad_repository import persist_broad_jobs
from jobintel.db.session import SessionLocal
from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job
from jobintel.resume.service import load_universal_profile

router = APIRouter(prefix="/companion", tags=["Browser Companion"])


def require_token(token: str | None) -> None:
    expected = os.getenv("JOBINTEL_COMPANION_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503, detail="Browser companion is not configured."
        )
    if token is None or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid companion token.")


class CaptureRequest(BaseModel):
    portal: str = "browser"
    title: str
    company: str
    location: str | None = None
    description: str | None = None
    url: HttpUrl


@router.get("/profile")
def profile(x_jobintel_token: str | None = Header(default=None)):
    require_token(x_jobintel_token)
    candidate = load_universal_profile()
    if candidate is None:
        raise HTTPException(
            status_code=404, detail="Universal candidate profile not found."
        )
    answers = build_application_answers(candidate).to_dict()
    answers["expected_compensation"] = None
    return {"answers": answers, "review_required": True, "auto_submit": False}


@router.post("/capture")
def capture(
    payload: CaptureRequest, x_jobintel_token: str | None = Header(default=None)
):
    require_token(x_jobintel_token)
    normalized = "|".join(
        [
            payload.portal.strip().lower(),
            payload.company.strip().lower(),
            payload.title.strip().lower(),
            (payload.location or "").strip().lower(),
            str(payload.url),
        ]
    )
    fingerprint = hashlib.sha256(normalized.encode()).hexdigest()
    host = urlparse(str(payload.url)).netloc or payload.portal
    fetched = FetchedJob(
        job=Job(
            source=payload.portal.strip().lower() or "browser",
            source_identifier=host,
            external_id=fingerprint[:24],
            company=payload.company.strip(),
            title=payload.title.strip(),
            location=payload.location,
            description=payload.description,
            department=None,
            apply_url=payload.url,
            posted_at=None,
            updated_at=None,
            fingerprint=fingerprint,
        ),
        raw=payload.model_dump(mode="json"),
    )
    with SessionLocal() as session:
        result = persist_broad_jobs(session=session, fetched_jobs=[fetched])
        session.commit()
    return {
        "captured": True,
        "new": result.new,
        "matched_existing": result.matched_existing,
        "existing_source": result.existing_source,
    }
