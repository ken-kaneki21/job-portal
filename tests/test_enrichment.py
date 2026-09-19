import pytest

from jobintel.enrichment.extractor import (
    EXTRACTOR_VERSION,
    classify_skill_context,
    extract_deal_breakers,
    extract_education,
    extract_employment_type,
    extract_experience_range,
    extract_job_enrichment,
    extract_responsibilities,
    extract_seniority,
    extract_skill_names,
    normalize_text,
    phrase_exists,
    SKILL_PATTERNS,
)


def test_extractor_version_exists():
    assert EXTRACTOR_VERSION == "deterministic_v2"


def test_normalize_text_collapses_whitespace():
    result = normalize_text(
        "  Python   SQL \n Snowflake  "
    )

    assert result == "Python SQL Snowflake"


def test_phrase_exists_matches_whole_phrase():
    assert phrase_exists(
        "Strong Python and SQL skills",
        "python",
    )

    assert not phrase_exists(
        "We use Pythonic coding practices",
        "python",
    )


def test_skill_extraction_detects_aliases():
    result = extract_skill_names(
        (
            "Experience with Py Spark, ADF, "
            "Postgres and PowerBI."
        ),
        SKILL_PATTERNS,
    )

    assert "pyspark" in result
    assert "azure data factory" in result
    assert "postgresql" in result
    assert "power bi" in result


@pytest.mark.parametrize(
    (
        "description",
        "minimum",
        "maximum",
    ),
    [
        (
            "3-5 years of experience",
            3,
            5,
        ),
        (
            "3 to 5 years experience",
            3,
            5,
        ),
        (
            "3–5 years of experience",
            3,
            5,
        ),
        (
            "Minimum of 4 years experience",
            4,
            None,
        ),
        (
            "At least 5 yrs experience",
            5,
            None,
        ),
        (
            "3+ years of experience",
            3,
            None,
        ),
        (
            "4 years of experience required",
            4,
            None,
        ),
    ],
)
def test_experience_extraction(
    description,
    minimum,
    maximum,
):
    result = extract_experience_range(
        description
    )

    assert result == (
        minimum,
        maximum,
    )


def test_experience_unknown_when_not_present():
    assert extract_experience_range(
        "Strong Python and SQL skills required"
    ) == (
        None,
        None,
    )


@pytest.mark.parametrize(
    (
        "title",
        "description",
        "expected",
    ),
    [
        (
            "Staff Data Engineer",
            "",
            "staff_principal",
        ),
        (
            "Principal Data Engineer",
            "",
            "staff_principal",
        ),
        (
            "Lead Data Engineer",
            "",
            "lead_manager",
        ),
        (
            "Data Engineering Manager",
            "",
            "lead_manager",
        ),
        (
            "Senior Data Engineer",
            "",
            "senior",
        ),
        (
            "Data Engineer Intern",
            "",
            "intern",
        ),
        (
            "Data Engineer",
            "Entry-level opportunity for graduates",
            "entry",
        ),
        (
            "Data Engineer",
            "",
            "mid",
        ),
    ],
)
def test_seniority_extraction(
    title,
    description,
    expected,
):
    assert extract_seniority(
        title,
        description,
    ) == expected


@pytest.mark.parametrize(
    (
        "text",
        "expected",
    ),
    [
        (
            "This is a full-time position.",
            "full_time",
        ),
        (
            "Permanent employee position.",
            "full_time",
        ),
        (
            "Six month contractual opportunity.",
            "contract",
        ),
        (
            "Summer internship role.",
            "internship",
        ),
        (
            "Part-time position.",
            "part_time",
        ),
    ],
)
def test_employment_type(
    text,
    expected,
):
    assert extract_employment_type(
        text
    ) == expected


def test_unknown_employment_type():
    assert extract_employment_type(
        "Work with our data engineering team."
    ) is None


@pytest.mark.parametrize(
    (
        "text",
        "expected",
    ),
    [
        (
            "Bachelor's degree in Computer Science required.",
            "bachelors",
        ),
        (
            "B.Tech in Computer Science required.",
            "bachelors",
        ),
        (
            "Master's degree preferred.",
            "masters",
        ),
        (
            "M.Tech in engineering preferred.",
            "masters",
        ),
        (
            "Degree in computer science required.",
            "degree",
        ),
    ],
)
def test_education_extraction(
    text,
    expected,
):
    assert extract_education(
        text
    ) == expected


def test_required_and_preferred_skill_context():
    description = """
Requirements:
Python, SQL and Snowflake are required.

Nice to have:
Kafka and Terraform experience.
"""

    required, preferred = (
        classify_skill_context(
            description
        )
    )

    assert set(required) == {
        "python",
        "sql",
        "snowflake",
    }

    assert set(preferred) == {
        "kafka",
        "terraform",
    }


def test_unclassified_skills_default_to_required():
    description = """
We use Python, SQL, Airflow and Snowflake
to build production data pipelines.
"""

    required, preferred = (
        classify_skill_context(
            description
        )
    )

    assert {
        "python",
        "sql",
        "airflow",
        "snowflake",
    }.issubset(
        set(required)
    )

    assert preferred == []


def test_required_takes_priority_over_preferred():
    description = """
Python is required.
Python is also listed as a nice to have skill.
"""

    required, preferred = (
        classify_skill_context(
            description
        )
    )

    assert "python" in required
    assert "python" not in preferred


def test_responsibilities_are_extracted():
    description = """
Build scalable ETL pipelines for analytics.
Design reliable batch processing systems.
Collaborate with analysts and engineers.
Python and SQL knowledge required.
"""

    result = extract_responsibilities(
        description
    )

    assert any(
        "Build scalable ETL pipelines"
        in item
        for item in result
    )

    assert any(
        "Design reliable batch processing"
        in item
        for item in result
    )

    assert any(
        "Collaborate with analysts"
        in item
        for item in result
    )


def test_deal_breakers_are_detected():
    description = """
This position requires an active security clearance.
Candidates must work onsite only.
Night shift availability is required.
Willingness to travel is required.
No visa sponsorship is available.
"""

    result = extract_deal_breakers(
        description
    )

    assert set(result) == {
        "security_clearance",
        "onsite_only",
        "night_shift",
        "travel_required",
        "visa_restriction",
    }


def test_clean_job_has_no_deal_breakers():
    result = extract_deal_breakers(
        (
            "Remote data engineering role "
            "using Python and SQL."
        )
    )

    assert result == []


def test_end_to_end_job_enrichment():
    description = """
We are hiring a full-time Data Engineer.

Requirements:
3-5 years of experience.
Python, SQL, PySpark and Airflow are required.
Experience with AWS and Snowflake.
Bachelor's degree in Computer Science.

Nice to have:
dbt and Terraform.

Responsibilities:
Build scalable ETL pipelines.
Design reliable cloud data workflows.
Collaborate with engineering teams.
"""

    result = extract_job_enrichment(
        title="Senior Data Engineer",
        description=description,
    )

    assert (
        result.minimum_experience_years
        == 3
    )

    assert (
        result.maximum_experience_years
        == 5
    )

    assert result.seniority == "senior"

    assert (
        result.employment_type
        == "full_time"
    )

    assert result.education == "bachelors"

    assert {
        "python",
        "sql",
        "pyspark",
        "airflow",
        "snowflake",
    }.issubset(
        set(result.required_skills)
    )

    assert {
        "dbt",
        "terraform",
    }.issubset(
        set(result.preferred_skills)
    )

    assert "aws" in result.cloud_platforms

    assert (
        "snowflake"
        in result.data_platforms
    )

    assert (
        len(result.responsibilities)
        >= 2
    )


def test_extractor_is_deterministic():
    description = """
Requirements:
Python, SQL and Snowflake.
3+ years of experience.

Nice to have:
Airflow and dbt.
"""

    first = extract_job_enrichment(
        title="Data Engineer",
        description=description,
    )

    second = extract_job_enrichment(
        title="Data Engineer",
        description=description,
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )


def test_empty_description_is_supported():
    result = extract_job_enrichment(
        title="Data Engineer",
        description=None,
    )

    assert (
        result.minimum_experience_years
        is None
    )

    assert (
        result.maximum_experience_years
        is None
    )

    assert result.seniority == "mid"

    assert result.required_skills == []
    assert result.preferred_skills == []
    assert result.cloud_platforms == []
    assert result.data_platforms == []
    assert result.responsibilities == []
    assert result.deal_breakers == []