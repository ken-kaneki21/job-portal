from __future__ import annotations

from jobintel.resume.structured import (
    extract_resume_structure,
    split_resume_sections,
)

SAMPLE_RESUME = """
SAURABH
Bangalore | +91-9352287355 | saurabhbsv1@gmail.com | LinkedIn | GitHub

PROFILE SUMMARY
Data Engineer with 2+ years of experience building production ETL/ELT systems and AI-assisted data tooling across Snowflake, dbt, Python,
Azure Data Factory, and Airflow. Built pipelines processing 100M+ rows.

TECHNICAL SKILLS
Languages: Python, SQL, Bash
Data & AI Engineering: Snowflake, dbt, Airflow, Azure Data Factory, PostgreSQL, ETL/ELT

EXPERIENCE
Data Engineer | Impilos Analytics Private Ltd. April 2026 – Present
• Built and maintained Python, Snowflake, dbt, and Azure Data Factory pipelines processing 100M+ rows.
• Developed an LLM-assisted workflow migration framework.

Data Analyst | Code Era Technologies Pvt. Ltd. July 2024 – April 2026
• Built SQL analytics and reporting workflows.
• Built a LangChain/OpenAI document-processing pipeline.

PROJECTS
JobLens - AI Job Intelligence & Resume Matching Platform [Python · Airflow · dbt · PostgreSQL · OpenAI
API · FastAPI ] 2025
• Built an end-to-end job intelligence pipeline aggregating 10K+ listings.
• Developed semantic resume-to-job matching.

Pipeline Conversion Toolkit [Python · SQL · dbt · OpenAI API · FastAPI · Docker · GitHub Actions ] 2026
• Built a compiler-style migration engine.
• Built an evaluation harness for generated pipelines.

EDUCATION & ACHIEVEMENTS
B.Tech, Aerospace Engineering — IIEST, Shibpur | Jun 2024
JEE Main: AIR 4,599 | GATE 2024: AIR 320 | HackerRank SQL (Advanced): Verified

CERTIFICATIONS
Google Advanced Data Analytics | MS Power BI Data Analyst | Azure AI Fundamentals (AI-900) | Azure ML Pipelines | Applied Statistics
(DeepLearning.AI) | IBM GenAI Data Analyst
""".strip()


def test_split_resume_sections():
    sections = split_resume_sections(
        SAMPLE_RESUME,
    )

    assert "summary" in sections
    assert "skills" in sections
    assert "experience" in sections
    assert "projects" in sections
    assert "education" in sections
    assert "certifications" in sections


def test_extract_identity():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert result.identity.full_name == "SAURABH"

    assert result.identity.email == "saurabhbsv1@gmail.com"

    assert result.identity.location == "Bangalore"

    assert result.identity.phone is not None


def test_extract_headline():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert result.headline == "Data Engineer"


def test_extract_summary():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert result.summary is not None

    assert "100M+ rows" in result.summary


def test_extract_experience():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert len(result.experience) == 2

    first = result.experience[0]

    assert first.title == "Data Engineer"

    assert first.company == "Impilos Analytics Private Ltd."

    assert first.start_date == "April 2026"

    assert first.end_date == "Present"

    assert "Python" in first.skills
    assert "Snowflake" in first.skills
    assert "dbt" in first.skills


def test_extract_second_experience():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    second = result.experience[1]

    assert second.title == "Data Analyst"

    assert second.company == "Code Era Technologies Pvt. Ltd."

    assert second.start_date == "July 2024"

    assert second.end_date == "April 2026"


def test_total_experience():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert result.total_experience_years is not None

    assert result.total_experience_years >= 2.0


def test_extract_projects():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert len(result.projects) == 2

    assert result.projects[0].name == (
        "JobLens - AI Job Intelligence & Resume Matching Platform"
    )

    assert "Python" in result.projects[0].skills

    assert result.projects[1].name == "Pipeline Conversion Toolkit"

    assert "Docker" in result.projects[1].skills


def test_extract_education():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert len(result.education) == 1

    education = result.education[0]

    assert education.degree == "B.Tech"

    assert education.field == "Aerospace Engineering"

    assert education.institution == "IIEST, Shibpur"

    assert education.end_year == 2024


def test_extract_certifications():
    result = extract_resume_structure(
        SAMPLE_RESUME,
    )

    assert result.certifications == [
        "Google Advanced Data Analytics",
        "MS Power BI Data Analyst",
        "Azure AI Fundamentals (AI-900)",
        "Azure ML Pipelines",
        "Applied Statistics (DeepLearning.AI)",
        "IBM GenAI Data Analyst",
    ]
