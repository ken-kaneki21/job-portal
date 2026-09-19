from types import SimpleNamespace

from jobintel.application_assets.generator import (
    GENERATOR_VERSION,
    build_missing_skills,
    build_skills_to_emphasize,
    generate_application_assets,
)


def make_profile():
    return SimpleNamespace(
        name="data_engineer",
        core_skills=[
            "Python",
            "SQL",
            "PySpark",
            "Snowflake",
            "Airflow",
        ],
        secondary_skills=[
            "AWS",
            "Azure",
            "dbt",
            "Databricks",
        ],
    )


def make_job():
    return SimpleNamespace(
        id=1,
        title="Data Engineer",
        company="Example Company",
        location="Bangalore, Karnataka",
    )


def make_enrichment():
    return SimpleNamespace(
        content_hash="enrichment-hash",
    )


def make_gap():
    return SimpleNamespace(
        content_hash="gap-hash",
        matched_required_skills=[
            "Python",
            "SQL",
            "Airflow",
        ],
        missing_required_skills=[
            "Kafka",
        ],
        matched_preferred_skills=[
            "AWS",
        ],
        missing_preferred_skills=[
            "Terraform",
        ],
        matched_platforms=[
            "Snowflake",
        ],
        missing_platforms=[
            "GCP",
        ],
        experience_fit="meets_requirement",
    )


def make_ranking():
    return SimpleNamespace(
        score=82.5,
        bucket="high_confidence",
    )


def test_generator_version_exists():
    assert GENERATOR_VERSION
    assert isinstance(
        GENERATOR_VERSION,
        str,
    )


def test_skills_to_emphasize_only_contains_profile_skills():
    profile = make_profile()
    gap = make_gap()

    result = build_skills_to_emphasize(
        profile=profile,
        gap=gap,
    )

    normalized = {value.lower() for value in result}

    assert "python" in normalized
    assert "sql" in normalized
    assert "aws" in normalized
    assert "snowflake" in normalized

    assert "kafka" not in normalized
    assert "terraform" not in normalized


def test_missing_skills_combines_gap_categories():
    gap = make_gap()

    result = build_missing_skills(gap)

    assert "Kafka" in result
    assert "Terraform" in result
    assert "GCP" in result


def test_application_assets_are_generated():
    assets = generate_application_assets(
        profile=make_profile(),
        job=make_job(),
        enrichment=make_enrichment(),
        gap=make_gap(),
        ranking=make_ranking(),
    )

    assert assets.recruiter_dm
    assert assets.email_subject
    assert assets.email_body
    assert assets.cover_note
    assert assets.resume_summary

    assert assets.skills_to_emphasize
    assert assets.missing_skills_warning
    assert assets.resume_bullets_to_emphasize
    assert assets.interview_talking_points


def test_generated_assets_reference_target_job():
    assets = generate_application_assets(
        profile=make_profile(),
        job=make_job(),
        enrichment=make_enrichment(),
        gap=make_gap(),
        ranking=make_ranking(),
    )

    assert "Data Engineer" in assets.recruiter_dm

    assert "Example Company" in assets.recruiter_dm

    assert "Data Engineer" in assets.email_subject

    assert "Example Company" in assets.email_subject


def test_assets_do_not_claim_missing_skill():
    assets = generate_application_assets(
        profile=make_profile(),
        job=make_job(),
        enrichment=make_enrichment(),
        gap=make_gap(),
        ranking=make_ranking(),
    )

    recruiter_dm = assets.recruiter_dm.lower()

    resume_summary = assets.resume_summary.lower()

    assert "kafka" not in recruiter_dm
    assert "terraform" not in recruiter_dm

    assert "kafka" not in resume_summary
    assert "terraform" not in resume_summary


def test_generator_is_deterministic():
    inputs = {
        "profile": make_profile(),
        "job": make_job(),
        "enrichment": make_enrichment(),
        "gap": make_gap(),
        "ranking": make_ranking(),
    }

    first = generate_application_assets(**inputs)

    second = generate_application_assets(**inputs)

    assert first.to_dict() == second.to_dict()
