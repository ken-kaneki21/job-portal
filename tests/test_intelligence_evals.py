from types import SimpleNamespace

from jobintel.gap_analysis.analyzer import (
    analyze_job_gap,
)


def make_profile():
    return SimpleNamespace(
        name="data_engineer",
        experience_years=4.0,
        core_skills=[
            "Python",
            "SQL",
            "PySpark",
            "Snowflake",
            "Airflow",
            "Azure Data Factory",
        ],
        secondary_skills=[
            "AWS",
            "Azure",
            "dbt",
            "Databricks",
            "PostgreSQL",
            "Power BI",
        ],
    )


def make_enrichment(
    *,
    required_skills,
    preferred_skills=None,
    cloud_platforms=None,
    data_platforms=None,
    minimum_experience_years=None,
    deal_breakers=None,
):
    return SimpleNamespace(
        required_skills=required_skills,
        preferred_skills=(
            preferred_skills or []
        ),
        cloud_platforms=(
            cloud_platforms or []
        ),
        data_platforms=(
            data_platforms or []
        ),
        minimum_experience_years=(
            minimum_experience_years
        ),
        deal_breakers=(
            deal_breakers or []
        ),
    )


def test_good_fit_beats_weak_fit():
    profile = make_profile()

    good_job = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
            "PySpark",
            "Snowflake",
        ],
        preferred_skills=[
            "Airflow",
            "dbt",
        ],
        cloud_platforms=[
            "AWS",
        ],
        minimum_experience_years=3,
    )

    weak_job = make_enrichment(
        required_skills=[
            "Java",
            "Kafka",
            "Terraform",
            "Kubernetes",
        ],
        preferred_skills=[
            "Go",
        ],
        cloud_platforms=[
            "GCP",
        ],
        minimum_experience_years=3,
    )

    good = analyze_job_gap(
        profile=profile,
        enrichment=good_job,
    )

    weak = analyze_job_gap(
        profile=profile,
        enrichment=weak_job,
    )

    assert (
        good.gap_score
        > weak.gap_score
    )

    assert (
        good.required_skill_match_ratio
        > weak.required_skill_match_ratio
    )


def test_matching_role_beats_experience_stretch():
    profile = make_profile()

    matching = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
            "Snowflake",
        ],
        preferred_skills=[
            "Airflow",
        ],
        minimum_experience_years=3,
    )

    stretch = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
            "Snowflake",
        ],
        preferred_skills=[
            "Airflow",
        ],
        minimum_experience_years=7,
    )

    matching_result = (
        analyze_job_gap(
            profile=profile,
            enrichment=matching,
        )
    )

    stretch_result = (
        analyze_job_gap(
            profile=profile,
            enrichment=stretch,
        )
    )

    assert (
        matching_result.gap_score
        > stretch_result.gap_score
    )

    assert (
        matching_result.experience_fit
        == "meets"
    )

    assert (
        stretch_result.experience_fit
        == "below_requirement"
    )


def test_missing_required_skill_hurts_more_than_preferred():
    profile = make_profile()

    missing_required = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
            "Kafka",
        ],
        preferred_skills=[
            "Airflow",
        ],
    )

    missing_preferred = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
        ],
        preferred_skills=[
            "Airflow",
            "Kafka",
        ],
    )

    required_result = (
        analyze_job_gap(
            profile=profile,
            enrichment=missing_required,
        )
    )

    preferred_result = (
        analyze_job_gap(
            profile=profile,
            enrichment=missing_preferred,
        )
    )

    assert (
        preferred_result.gap_score
        > required_result.gap_score
    )


def test_deal_breaker_job_scores_lower():
    profile = make_profile()

    clean_job = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
            "Snowflake",
        ],
        minimum_experience_years=3,
    )

    blocker_job = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
            "Snowflake",
        ],
        minimum_experience_years=3,
        deal_breakers=[
            "US security clearance required",
        ],
    )

    clean_result = (
        analyze_job_gap(
            profile=profile,
            enrichment=clean_job,
        )
    )

    blocker_result = (
        analyze_job_gap(
            profile=profile,
            enrichment=blocker_job,
        )
    )

    assert (
        clean_result.gap_score
        > blocker_result.gap_score
    )

    assert (
        blocker_result.deal_breakers
        == [
            "US security clearance required"
        ]
    )


def test_empty_jd_is_neutral_not_high_confidence():
    result = analyze_job_gap(
        profile=make_profile(),
        enrichment=make_enrichment(
            required_skills=[],
        ),
    )

    assert result.gap_score == 50.0

    assert (
        result.required_skill_match_ratio
        == 0.0
    )

    assert (
        result.experience_fit
        == "not_specified"
    )


def test_unknown_candidate_experience_is_not_perfect():
    profile = SimpleNamespace(
        name="data_engineer",
        core_skills=[
            "Python",
            "SQL",
        ],
        secondary_skills=[],
    )

    job = make_enrichment(
        required_skills=[
            "Python",
            "SQL",
        ],
        minimum_experience_years=5,
    )

    result = analyze_job_gap(
        profile=profile,
        enrichment=job,
    )

    assert (
        result.experience_fit
        == "unknown"
    )

    assert (
        result.experience_gap_years
        is None
    )

    assert result.gap_score < 100