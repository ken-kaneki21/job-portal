from types import SimpleNamespace

import pytest

from jobintel.gap_analysis.analyzer import (
    ANALYZER_VERSION,
    analyze_experience,
    analyze_job_gap,
    calculate_gap_score,
    calculate_ratio,
    get_profile_experience,
    normalize_collection,
    normalize_skill,
)


def make_profile(
    *,
    experience_years=4.0,
    core_skills=None,
    secondary_skills=None,
):
    return SimpleNamespace(
        name="data_engineer",
        experience_years=experience_years,
        core_skills=(
            core_skills
            if core_skills is not None
            else [
                "Python",
                "SQL",
                "PySpark",
                "Snowflake",
                "Airflow",
                "Azure Data Factory",
            ]
        ),
        secondary_skills=(
            secondary_skills
            if secondary_skills is not None
            else [
                "AWS",
                "Azure",
                "dbt",
                "Databricks",
                "PostgreSQL",
                "Power BI",
            ]
        ),
    )


def make_enrichment(
    *,
    required_skills=None,
    preferred_skills=None,
    cloud_platforms=None,
    data_platforms=None,
    minimum_experience_years=None,
    deal_breakers=None,
):
    return SimpleNamespace(
        required_skills=(required_skills if required_skills is not None else []),
        preferred_skills=(preferred_skills if preferred_skills is not None else []),
        cloud_platforms=(cloud_platforms if cloud_platforms is not None else []),
        data_platforms=(data_platforms if data_platforms is not None else []),
        minimum_experience_years=(minimum_experience_years),
        deal_breakers=(deal_breakers if deal_breakers is not None else []),
    )


def test_analyzer_version_exists():
    assert ANALYZER_VERSION == "deterministic_gap_v2"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ADF", "azure data factory"),
        (
            "Azure Data Factory",
            "azure data factory",
        ),
        ("Py Spark", "pyspark"),
        ("Apache Spark", "spark"),
        ("Postgres", "postgresql"),
        ("PowerBI", "power bi"),
        (
            "Amazon Web Services",
            "aws",
        ),
        (
            "Google Cloud Platform",
            "gcp",
        ),
        ("Data Build Tool", "dbt"),
    ],
)
def test_skill_alias_normalization(
    raw,
    expected,
):
    assert normalize_skill(raw) == expected


def test_collection_normalization_deduplicates_aliases():
    result = normalize_collection(
        [
            "ADF",
            "Azure Data Factory",
            "PySpark",
            "Py Spark",
        ]
    )

    assert result == {
        "azure data factory",
        "pyspark",
    }


def test_empty_expected_ratio_is_zero_not_perfect():
    result = calculate_ratio(
        matched=set(),
        expected=set(),
    )

    assert result == 0.0


def test_ratio_is_calculated_correctly():
    result = calculate_ratio(
        matched={
            "python",
            "sql",
        },
        expected={
            "python",
            "sql",
            "pyspark",
            "airflow",
        },
    )

    assert result == 0.5


def test_profile_experience_uses_explicit_experience():
    profile = make_profile(experience_years=4.5)

    assert get_profile_experience(profile) == 4.5


def test_missing_profile_experience_is_unknown():
    profile = SimpleNamespace(
        core_skills=[],
        secondary_skills=[],
    )

    assert get_profile_experience(profile) is None


def test_experience_not_specified():
    fit, gap = analyze_experience(
        required_years=None,
        profile_experience=4.0,
    )

    assert fit == "not_specified"
    assert gap is None


def test_experience_meets_requirement():
    fit, gap = analyze_experience(
        required_years=3,
        profile_experience=4.0,
    )

    assert fit == "meets"
    assert gap == 0.0


def test_experience_below_requirement():
    fit, gap = analyze_experience(
        required_years=6,
        profile_experience=4.0,
    )

    assert fit == "below_requirement"
    assert gap == 2.0


def test_unknown_candidate_experience():
    fit, gap = analyze_experience(
        required_years=5,
        profile_experience=None,
    )

    assert fit == "unknown"
    assert gap is None


def test_empty_jd_returns_neutral_gap_score():
    result = calculate_gap_score(
        required_skills=set(),
        required_ratio=0.0,
        preferred_skills=set(),
        preferred_ratio=0.0,
        platforms=set(),
        platform_ratio=0.0,
        required_experience=None,
        experience_fit="not_specified",
        deal_breakers=[],
    )

    assert result == 50.0


def test_full_match_scores_above_partial_match():
    full = calculate_gap_score(
        required_skills={
            "python",
            "sql",
        },
        required_ratio=1.0,
        preferred_skills={
            "airflow",
        },
        preferred_ratio=1.0,
        platforms={
            "aws",
        },
        platform_ratio=1.0,
        required_experience=3,
        experience_fit="meets",
        deal_breakers=[],
    )

    partial = calculate_gap_score(
        required_skills={
            "python",
            "sql",
        },
        required_ratio=0.5,
        preferred_skills={
            "airflow",
        },
        preferred_ratio=0.0,
        platforms={
            "aws",
        },
        platform_ratio=0.0,
        required_experience=3,
        experience_fit="meets",
        deal_breakers=[],
    )

    assert full > partial


def test_deal_breakers_reduce_score():
    no_breaker = calculate_gap_score(
        required_skills={
            "python",
            "sql",
        },
        required_ratio=1.0,
        preferred_skills=set(),
        preferred_ratio=0.0,
        platforms=set(),
        platform_ratio=0.0,
        required_experience=None,
        experience_fit="not_specified",
        deal_breakers=[],
    )

    with_breaker = calculate_gap_score(
        required_skills={
            "python",
            "sql",
        },
        required_ratio=1.0,
        preferred_skills=set(),
        preferred_ratio=0.0,
        platforms=set(),
        platform_ratio=0.0,
        required_experience=None,
        experience_fit="not_specified",
        deal_breakers=["security clearance required"],
    )

    assert no_breaker > with_breaker


def test_matching_job_detects_required_skills():
    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=make_enrichment(
            required_skills=[
                "Python",
                "SQL",
                "PySpark",
            ],
            preferred_skills=[
                "Airflow",
                "dbt",
            ],
            cloud_platforms=[
                "AWS",
            ],
            data_platforms=[
                "Snowflake",
            ],
            minimum_experience_years=3,
        ),
    )

    assert analysis.missing_required_skills == []

    assert set(analysis.matched_required_skills) == {
        "python",
        "sql",
        "pyspark",
    }

    assert analysis.required_skill_match_ratio == 1.0

    assert analysis.experience_fit == "meets"

    assert analysis.experience_gap_years == 0.0


def test_missing_required_skills_are_reported():
    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=make_enrichment(
            required_skills=[
                "Python",
                "SQL",
                "Kafka",
                "Terraform",
            ],
        ),
    )

    assert set(analysis.matched_required_skills) == {
        "python",
        "sql",
    }

    assert set(analysis.missing_required_skills) == {
        "kafka",
        "terraform",
    }

    assert analysis.required_skill_match_ratio == 0.5


def test_aliases_match_profile_skills():
    profile = make_profile(
        core_skills=[
            "Azure Data Factory",
            "PySpark",
        ],
        secondary_skills=[],
    )

    enrichment = make_enrichment(
        required_skills=[
            "ADF",
            "Py Spark",
        ]
    )

    analysis = analyze_job_gap(
        profile=profile,
        enrichment=enrichment,
    )

    assert analysis.missing_required_skills == []

    assert set(analysis.matched_required_skills) == {
        "azure data factory",
        "pyspark",
    }


def test_experience_gap_is_exposed_in_analysis():
    analysis = analyze_job_gap(
        profile=make_profile(experience_years=4),
        enrichment=make_enrichment(
            required_skills=[
                "Python",
                "SQL",
            ],
            minimum_experience_years=6,
        ),
    )

    assert analysis.experience_fit == "below_requirement"

    assert analysis.experience_gap_years == 2.0

    assert "Experience gap: 2.0 years" in analysis.fit_summary


def test_sparse_jd_does_not_score_100():
    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=make_enrichment(
            required_skills=[
                "Python",
            ],
        ),
    )

    assert analysis.gap_score < 100.0
    assert analysis.gap_score > 50.0


def test_analysis_is_deterministic():
    profile = make_profile()

    enrichment = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
            "Kafka",
        ],
        preferred_skills=[
            "Airflow",
        ],
        cloud_platforms=[
            "AWS",
        ],
        minimum_experience_years=4,
    )

    first = analyze_job_gap(
        profile=profile,
        enrichment=enrichment,
    )

    second = analyze_job_gap(
        profile=profile,
        enrichment=enrichment,
    )

    assert first.to_dict() == second.to_dict()
