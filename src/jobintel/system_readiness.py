from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from jobintel.db.profile_repository import get_universal_profile_payload
from jobintel.profile.runtime import ACTIVE_PROFILE_NAME


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    database: str
    profile: str
    profile_name: str

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_readiness(
    session: Session,
    *,
    profile_name: str = ACTIVE_PROFILE_NAME,
) -> ReadinessResult:
    session.execute(text("SELECT 1"))

    profile_payload = get_universal_profile_payload(
        session,
        profile_name=profile_name,
    )

    profile_ready = profile_payload is not None

    return ReadinessResult(
        ready=profile_ready,
        database="connected",
        profile="available" if profile_ready else "missing",
        profile_name=profile_name,
    )
