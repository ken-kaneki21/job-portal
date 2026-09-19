import json
from pathlib import Path

from jobintel.profile.models import CandidateProfile


def load_profile(
    path: str | Path,
) -> CandidateProfile:
    profile_path = Path(path)

    with profile_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return CandidateProfile.model_validate(data)