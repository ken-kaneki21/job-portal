from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from jobintel.application_workflow.packet import (
    ApplicationPacketError,
    build_application_packet,
)
from jobintel.application_workflow.workday import build_workday_plan
from jobintel.db.session import SessionLocal
from jobintel.resume.service import load_universal_profile

router = APIRouter(tags=["Application Workflow"])


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def load_profile_or_404():
    profile = load_universal_profile()
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Universal candidate profile not found.",
        )
    return profile


@router.get("/jobs/{job_id}/application-packet")
def application_packet(
    job_id: int,
    session: Session = Depends(get_db),
):
    profile = load_profile_or_404()
    try:
        packet = build_application_packet(
            session=session,
            job_id=job_id,
            profile=profile,
        )
    except ApplicationPacketError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return packet.to_dict()


@router.get("/jobs/{job_id}/workday-plan")
def workday_plan(
    job_id: int,
    session: Session = Depends(get_db),
):
    profile = load_profile_or_404()
    try:
        packet = build_application_packet(
            session=session,
            job_id=job_id,
            profile=profile,
        )
    except ApplicationPacketError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_workday_plan(packet).to_dict()
