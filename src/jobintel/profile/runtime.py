from __future__ import annotations

import logging
import os
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from jobintel.db.profile_repository import (
    get_legacy_profile_payload,
)
from jobintel.db.session import (
    SessionLocal,
)
from jobintel.profile.loader import (
    load_profile,
)
from jobintel.profile.models import (
    CandidateProfile,
)

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_NAME = "universal"

DEFAULT_PROFILE_PATH = Path("profiles/generated_v2.json")

ACTIVE_PROFILE_NAME = (
    os.getenv(
        "JOBINTEL_PROFILE_NAME",
        DEFAULT_PROFILE_NAME,
    ).strip()
    or DEFAULT_PROFILE_NAME
)

ACTIVE_PROFILE_PATH = Path(
    os.getenv(
        "JOBINTEL_PROFILE_PATH",
        str(DEFAULT_PROFILE_PATH),
    ).strip()
    or str(DEFAULT_PROFILE_PATH)
)


def load_active_candidate_profile() -> CandidateProfile:
    try:
        with SessionLocal() as session:
            payload = get_legacy_profile_payload(
                session,
                profile_name=(ACTIVE_PROFILE_NAME),
            )

        if payload is not None:
            return CandidateProfile.model_validate(
                payload,
            )

    except SQLAlchemyError:
        logger.warning(
            (
                "Unable to load active candidate "
                "profile from the database; "
                "falling back to the configured "
                "JSON profile."
            ),
            exc_info=True,
        )

    return load_profile(ACTIVE_PROFILE_PATH)
