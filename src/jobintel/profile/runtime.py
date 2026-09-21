from __future__ import annotations

import os
from pathlib import Path

DEFAULT_PROFILE_NAME = "universal"
DEFAULT_PROFILE_PATH = Path("profiles/generated_v2.json")

ACTIVE_PROFILE_NAME = (
    os.getenv("JOBINTEL_PROFILE_NAME", DEFAULT_PROFILE_NAME).strip()
    or DEFAULT_PROFILE_NAME
)

ACTIVE_PROFILE_PATH = Path(
    os.getenv(
        "JOBINTEL_PROFILE_PATH",
        str(DEFAULT_PROFILE_PATH),
    ).strip()
    or str(DEFAULT_PROFILE_PATH)
)
