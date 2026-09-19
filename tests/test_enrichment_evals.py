from types import SimpleNamespace

from jobintel.enrichment.extractor import (
    extract_job_enrichment,
)
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


def test_good_jd_flows_from_text_to_high_gap_fit():
    description = """
Requirements:
3+ years of experience.
Python, SQL, PySpark and Snowflake required.
AWS experience required.

Nice to have:
Airflow and dbt.

Responsibilities:
Build scalable ETL pipelines.
Design production data workflows.
"""

    enrichment = extract_job_enrichment(
        title="Data Engineer",
        description=description,
    )

    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=enrichment,
    )

    assert enrichment.minimum_experience_years == 3

    assert analysis.experience_fit == "meets"

    assert analysis.required_skill_match_ratio == 1.0

    assert analysis.gap_score > 70


def test_weak_jd_produces_lower_fit():
    description = """
Requirements:
3+ years of experience.
Java, Kafka, Kubernetes and Terraform required.
GCP experience required.

Nice to have:
FastAPI.

Responsibilities:
Build distributed streaming systems.
"""

    enrichment = extract_job_enrichment(
        title="Data Engineer",
        description=description,
    )

    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=enrichment,
    )

    assert analysis.required_skill_match_ratio < 0.5

    assert len(analysis.missing_required_skills) > 0


def test_good_jd_scores_above_weak_jd():
    profile = make_profile()

    good_description = """
Requirements:
Python, SQL, PySpark and Snowflake required.
3+ years of experience.

Nice to have:
Airflow and dbt.
"""

    weak_description = """
Requirements:
Java, Kafka, Kubernetes and Terraform required.
3+ years of experience.

Nice to have:
GCP.
"""

    good_enrichment = extract_job_enrichment(
        title="Data Engineer",
        description=good_description,
    )

    weak_enrichment = extract_job_enrichment(
        title="Data Engineer",
        description=weak_description,
    )

    good_analysis = analyze_job_gap(
        profile=profile,
        enrichment=good_enrichment,
    )

    weak_analysis = analyze_job_gap(
        profile=profile,
        enrichment=weak_enrichment,
    )

    assert good_analysis.gap_score > weak_analysis.gap_score


def test_extracted_experience_changes_gap_fit():
    profile = make_profile()

    matching = extract_job_enrichment(
        title="Data Engineer",
        description="""
Python and SQL required.
3+ years of experience.
""",
    )

    stretch = extract_job_enrichment(
        title="Senior Data Engineer",
        description="""
Python and SQL required.
7+ years of experience.
""",
    )

    matching_result = analyze_job_gap(
        profile=profile,
        enrichment=matching,
    )

    stretch_result = analyze_job_gap(
        profile=profile,
        enrichment=stretch,
    )

    assert matching_result.experience_fit == "meets"

    assert stretch_result.experience_fit == "below_requirement"

    assert matching_result.gap_score > stretch_result.gap_score


def test_extracted_aliases_flow_into_gap_matching():
    description = """
Requirements:
ADF, Py Spark and Postgres required.
"""

    enrichment = extract_job_enrichment(
        title="Data Engineer",
        description=description,
    )

    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=enrichment,
    )

    assert analysis.missing_required_skills == []

    assert {
        "azure data factory",
        "pyspark",
        "postgresql",
    }.issubset(set(analysis.matched_required_skills))


def test_sparse_jd_remains_neutralish_end_to_end():
    enrichment = extract_job_enrichment(
        title="Data Engineer",
        description=("Join our growing data team."),
    )

    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=enrichment,
    )

    assert enrichment.required_skills == []

    assert enrichment.minimum_experience_years is None

    assert analysis.gap_score == 50.0


def test_deal_breaker_flows_into_gap_analysis():
    description = """
Requirements:
Python and SQL required.
3+ years of experience.

Candidates must have an active security clearance.
"""

    enrichment = extract_job_enrichment(
        title="Data Engineer",
        description=description,
    )

    analysis = analyze_job_gap(
        profile=make_profile(),
        enrichment=enrichment,
    )

    assert "security_clearance" in enrichment.deal_breakers

    assert "security_clearance" in analysis.deal_breakers

    assert "Potential deal-breakers" in analysis.fit_summary
