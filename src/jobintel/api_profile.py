from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from jobintel.profile.universal import (
    UniversalCandidateProfile,
)
from jobintel.resume.parser import (
    ResumeParseError,
)
from jobintel.resume.service import (
    build_profile_from_resume,
    load_universal_profile,
    persist_profile,
)

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)


MAX_RESUME_BYTES = 10 * 1024 * 1024


@router.get("")
def get_profile():
    profile = load_universal_profile()

    if profile is None:
        return {
            "configured": False,
            "profile": None,
        }

    return {
        "configured": True,
        "profile": profile.model_dump(
            mode="json",
        ),
    }


@router.put("")
def update_profile(
    profile: UniversalCandidateProfile,
):
    persist_profile(
        profile,
    )

    return {
        "configured": True,
        "profile": profile.model_dump(
            mode="json",
        ),
    }


@router.post("/resume")
async def upload_resume(
    file: Annotated[
        UploadFile,
        File(...),
    ],
):
    filename = file.filename or "resume.pdf"

    if not filename.lower().endswith(
        ".pdf",
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are supported.",
        )

    content = await file.read()

    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Resume PDF exceeds the 10 MB limit.",
        )

    try:
        profile = build_profile_from_resume(
            filename=filename,
            content=content,
        )
    except ResumeParseError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    persist_profile(
        profile,
    )

    return {
        "message": "Resume parsed successfully.",
        "profile": profile.model_dump(
            mode="json",
        ),
    }
