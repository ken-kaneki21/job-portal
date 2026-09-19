from types import SimpleNamespace

from jobintel.application_assets.service import (
    build_content_hash,
)


def make_inputs(
    *,
    ranking_score: float = 80.0,
    enrichment_hash: str = "enrichment-1",
    gap_hash: str = "gap-1",
):
    job = SimpleNamespace(
        id=100,
        title="Data Engineer",
        company="Example Company",
    )

    enrichment = SimpleNamespace(
        content_hash=enrichment_hash,
    )

    gap = SimpleNamespace(
        content_hash=gap_hash,
    )

    ranking = SimpleNamespace(
        score=ranking_score,
        bucket="high_confidence",
    )

    return {
        "job": job,
        "enrichment": enrichment,
        "gap": gap,
        "ranking": ranking,
    }


def test_content_hash_is_deterministic():
    inputs = make_inputs()

    first = build_content_hash(
        **inputs
    )

    second = build_content_hash(
        **inputs
    )

    assert first == second


def test_content_hash_has_sha256_length():
    result = build_content_hash(
        **make_inputs()
    )

    assert len(result) == 64


def test_ranking_change_changes_hash():
    first = build_content_hash(
        **make_inputs(
            ranking_score=80.0
        )
    )

    second = build_content_hash(
        **make_inputs(
            ranking_score=90.0
        )
    )

    assert first != second


def test_enrichment_change_changes_hash():
    first = build_content_hash(
        **make_inputs(
            enrichment_hash="one"
        )
    )

    second = build_content_hash(
        **make_inputs(
            enrichment_hash="two"
        )
    )

    assert first != second


def test_gap_change_changes_hash():
    first = build_content_hash(
        **make_inputs(
            gap_hash="one"
        )
    )

    second = build_content_hash(
        **make_inputs(
            gap_hash="two"
        )
    )

    assert first != second