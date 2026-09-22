from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from jobintel.db.session import SessionLocal
from jobintel.system_readiness import evaluate_readiness
from jobintel.version import __version__

router = APIRouter(tags=["System"])


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/version")
def version():
    return {
        "service": "job-intelligence",
        "version": __version__,
    }


@router.get("/ready")
def ready(
    session: Session = Depends(get_db),
):
    try:
        result = evaluate_readiness(session)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {exc}",
        ) from exc

    if not result.ready:
        raise HTTPException(
            status_code=503,
            detail=result.to_dict(),
        )

    return result.to_dict()
