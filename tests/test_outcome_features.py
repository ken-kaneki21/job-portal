from types import SimpleNamespace

from jobintel.outcome_learning.features import extract_outcome_features
from jobintel.profile.models import CandidateProfile


def test_outcome_features_are_explainable():
    profile = CandidateProfile(
        name="universal",
        target_titles=["data engineer"],
        adjacent_titles=["data analyst"],
        exclude_titles=[],
        preferred_locations=["Bangalore"],
        allowed_countries=["India"],
        blocked_location_terms=[],
        core_skills=["python", "sql", "snowflake"],
        secondary_skills=["airflow"],
        max_preferred_experience_years=5,
        hard_max_experience_years=8,
    )

    job = SimpleNamespace(
        source="linkedin",
        title="Data Engineer",
        location="Bengaluru, India",
        description="3+ years Python SQL Snowflake experience.",
        department="Data",
    )

    ranking = SimpleNamespace(
        deterministic_score=72.0,
        semantic_score=7.2,
        gap_score=81.0,
    )

    features = extract_outcome_features(
        job=job,
        ranking=ranking,
        profile=profile,
    )

    assert features.source == "linkedin"
    assert features.title_family == "data_engineering"
    assert features.location_family == "bengaluru"
    assert features.experience_band == "3-4"
    assert "python" in features.skill_signature
