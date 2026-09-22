from __future__ import annotations

import jobintel.profile.runtime as runtime_module
import jobintel.resume.service as service_module
from jobintel.db.profile_repository import (
    get_legacy_profile_payload,
    get_universal_profile_payload,
)
from jobintel.profile.models import (
    CandidateProfile,
)
from jobintel.profile.universal import (
    CandidatePreferences,
    UniversalCandidateProfile,
)


def make_universal_profile() -> UniversalCandidateProfile:
    return UniversalCandidateProfile(
        profile_name="universal",
        headline=("Data Engineer"),
        summary=None,
        total_experience_years=3.0,
        role_families=[],
        core_skills=[
            "Python",
            "SQL",
        ],
        secondary_skills=[
            "Snowflake",
        ],
        tools=[],
        cloud_platforms=[
            "AWS",
        ],
        preferences=(
            CandidatePreferences(
                preferred_locations=[
                    "Bengaluru",
                ],
                allowed_countries=[
                    "India",
                ],
                blocked_location_terms=[],
                blocked_titles=[],
            )
        ),
    )


def make_legacy_payload() -> dict:
    return CandidateProfile(
        name="universal",
        target_titles=[
            "data engineer",
        ],
        adjacent_titles=[],
        exclude_titles=[],
        preferred_locations=[
            "Bengaluru",
        ],
        allowed_countries=[
            "India",
        ],
        blocked_location_terms=[],
        core_skills=[
            "Python",
            "SQL",
        ],
        secondary_skills=[
            "Snowflake",
        ],
        max_preferred_experience_years=5,
        hard_max_experience_years=8,
    ).model_dump(
        mode="json",
    )


def test_load_universal_profile_prefers_database(
    monkeypatch,
):
    profile = make_universal_profile()

    payload = profile.model_dump(
        mode="json",
    )

    class FakeSession:
        def __enter__(
            self,
        ):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            del (
                exc_type,
                exc_value,
                traceback,
            )

    monkeypatch.setattr(
        service_module,
        "SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        service_module,
        "get_universal_profile_payload",
        lambda session, profile_name: payload,
    )

    monkeypatch.setattr(
        service_module,
        "load_universal_profile_from_file",
        lambda: None,
    )

    loaded = service_module.load_universal_profile()

    assert loaded is not None

    assert loaded.profile_name == "universal"

    assert loaded.core_skills == [
        "Python",
        "SQL",
    ]


def test_load_universal_profile_falls_back_to_file(
    monkeypatch,
):
    fallback = make_universal_profile()

    class FakeSession:
        def __enter__(
            self,
        ):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            del (
                exc_type,
                exc_value,
                traceback,
            )

    monkeypatch.setattr(
        service_module,
        "SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        service_module,
        "get_universal_profile_payload",
        lambda session, profile_name: None,
    )

    monkeypatch.setattr(
        service_module,
        "load_universal_profile_from_file",
        lambda: fallback,
    )

    loaded = service_module.load_universal_profile()

    assert loaded is fallback


def test_runtime_profile_prefers_database(
    monkeypatch,
):
    payload = make_legacy_payload()

    class FakeSession:
        def __enter__(
            self,
        ):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            del (
                exc_type,
                exc_value,
                traceback,
            )

    monkeypatch.setattr(
        runtime_module,
        "SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        runtime_module,
        "get_legacy_profile_payload",
        lambda session, profile_name: payload,
    )

    loaded = runtime_module.load_active_candidate_profile()

    assert loaded.name == "universal"

    assert loaded.target_titles == [
        "data engineer",
    ]


def test_profile_repository_helpers_return_payloads():
    class Record:
        universal_payload = {"profile_name": ("universal")}

        legacy_payload = {"name": ("universal")}

    class FakeSession:
        def scalar(
            self,
            statement,
        ):
            del statement

            return Record()

    session = FakeSession()

    universal = get_universal_profile_payload(
        session,
        profile_name="universal",
    )

    legacy = get_legacy_profile_payload(
        session,
        profile_name="universal",
    )

    assert universal == {"profile_name": ("universal")}

    assert legacy == {"name": "universal"}
