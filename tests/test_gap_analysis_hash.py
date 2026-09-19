from types import SimpleNamespace

from jobintel.backfill_gap_analysis import (
    build_content_hash,
)


def make_profile(
    *,
    skills=None,
    experience=4.0,
):
    return SimpleNamespace(
        name="data_engineer",
        core_skills=(
            skills
            or [
                "Python",
                "SQL",
            ]
        ),
        secondary_skills=[
            "AWS",
        ],
        experience_years=(experience),
        years_of_experience=None,
    )


def make_enrichment(
    content_hash="enrichment-v1",
    extractor_version="deterministic_v2",
):
    return SimpleNamespace(
        content_hash=content_hash,
        extractor_version=extractor_version,
    )


def test_gap_hash_is_deterministic():
    profile = make_profile()
    enrichment = make_enrichment()

    first = build_content_hash(
        profile=profile,
        enrichment=enrichment,
    )

    second = build_content_hash(
        profile=profile,
        enrichment=enrichment,
    )

    assert first == second


def test_enrichment_change_invalidates_gap_hash():
    profile = make_profile()

    first = build_content_hash(
        profile=profile,
        enrichment=make_enrichment(content_hash="enrichment-v1"),
    )

    second = build_content_hash(
        profile=profile,
        enrichment=make_enrichment(content_hash="enrichment-v2"),
    )

    assert first != second


def test_extractor_version_change_invalidates_gap_hash():
    profile = make_profile()

    first = build_content_hash(
        profile=profile,
        enrichment=make_enrichment(extractor_version=("deterministic_v1")),
    )

    second = build_content_hash(
        profile=profile,
        enrichment=make_enrichment(extractor_version=("deterministic_v2")),
    )

    assert first != second


def test_profile_skill_change_invalidates_gap_hash():
    enrichment = make_enrichment()

    first = build_content_hash(
        profile=make_profile(
            skills=[
                "Python",
                "SQL",
            ]
        ),
        enrichment=enrichment,
    )

    second = build_content_hash(
        profile=make_profile(
            skills=[
                "Python",
                "SQL",
                "Kafka",
            ]
        ),
        enrichment=enrichment,
    )

    assert first != second


def test_experience_change_invalidates_gap_hash():
    enrichment = make_enrichment()

    first = build_content_hash(
        profile=make_profile(experience=3.0),
        enrichment=enrichment,
    )

    second = build_content_hash(
        profile=make_profile(experience=5.0),
        enrichment=enrichment,
    )

    assert first != second
