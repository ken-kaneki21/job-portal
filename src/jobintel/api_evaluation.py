from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from jobintel.db.session import SessionLocal
from jobintel.evaluation.service import run_offline_evaluation
from jobintel.profile.runtime import load_active_candidate_profile

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)


def get_db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@router.get("/ranking")
def ranking_evaluation(
    k: list[int] = Query(
        default=[
            5,
            10,
            20,
        ],
    ),
    session: Session = Depends(get_db),
):
    profile = load_active_candidate_profile()

    normalized = tuple(sorted({value for value in k if value > 0}))

    if not normalized:
        normalized = (
            5,
            10,
            20,
        )

    return run_offline_evaluation(
        session=session,
        profile=profile,
        ks=normalized,
    )
