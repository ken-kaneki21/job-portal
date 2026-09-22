from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from jobintel.db.session import SessionLocal
from jobintel.outcome_learning.service import (
    build_outcome_model,
    top_feature_stats,
)
from jobintel.profile.runtime import load_active_candidate_profile

router = APIRouter(prefix="/outcomes", tags=["Outcome Learning"])


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/summary")
def outcome_summary(session: Session = Depends(get_db)):
    profile = load_active_candidate_profile()
    model = build_outcome_model(session=session, profile=profile)
    return {
        "profile_name": profile.name,
        "sample_count": model.sample_count,
        "active": model.active,
        "global_mean": model.global_mean,
    }


@router.get("/features")
def outcome_features(
    limit: int = Query(50, ge=1, le=500),
    session: Session = Depends(get_db),
):
    profile = load_active_candidate_profile()
    model = build_outcome_model(session=session, profile=profile)
    stats = top_feature_stats(model, limit=limit)
    return {
        "profile_name": profile.name,
        "sample_count": model.sample_count,
        "active": model.active,
        "features": [stat.to_dict() for stat in stats],
    }
