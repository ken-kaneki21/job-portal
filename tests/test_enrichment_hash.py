from jobintel.backfill_enrichments import (
    build_content_hash,
)


def test_enrichment_hash_is_deterministic():
    first = build_content_hash(
        title="Data Engineer",
        description=(
            "Python SQL Snowflake"
        ),
    )

    second = build_content_hash(
        title="Data Engineer",
        description=(
            "Python SQL Snowflake"
        ),
    )

    assert first == second


def test_description_change_changes_hash():
    first = build_content_hash(
        title="Data Engineer",
        description="Python SQL",
    )

    second = build_content_hash(
        title="Data Engineer",
        description=(
            "Python SQL Snowflake"
        ),
    )

    assert first != second


def test_title_change_changes_hash():
    first = build_content_hash(
        title="Data Engineer",
        description="Python SQL",
    )

    second = build_content_hash(
        title="Senior Data Engineer",
        description="Python SQL",
    )

    assert first != second


def test_none_description_is_supported():
    result = build_content_hash(
        title="Data Engineer",
        description=None,
    )

    assert isinstance(
        result,
        str,
    )

    assert len(result) == 64