from __future__ import annotations

import re

SKILLS = [
    "Python",
    "SQL",
    "PySpark",
    "Spark",
    "Spark SQL",
    "Snowflake",
    "Databricks",
    "Airflow",
    "dbt",
    "Azure Data Factory",
    "ADF",
    "AWS",
    "Azure",
    "GCP",
    "BigQuery",
    "Kafka",
    "PostgreSQL",
    "MySQL",
    "Docker",
    "Kubernetes",
    "Git",
    "GitHub Actions",
    "CI/CD",
    "Power BI",
    "Tableau",
    "Microsoft Fabric",
    "FastAPI",
    "Redis",
    "Temporal",
    "OpenAI",
    "Groq",
    "LLM",
    "RAG",
    "Embeddings",
    "Vector Database",
    "pgvector",
    "Machine Learning",
    "Pandas",
    "NumPy",
    "Data Modeling",
    "ETL",
    "ELT",
    "Data Warehousing",
    "REST API",
    "Playwright",
    "Alteryx",
    "ClickHouse",
    "Palantir Foundry",
]


CORE_SKILL_PRIORITY = {
    "python",
    "sql",
    "pyspark",
    "spark",
    "snowflake",
    "databricks",
    "airflow",
    "dbt",
    "azure data factory",
    "aws",
    "azure",
    "gcp",
    "llm",
    "rag",
}


def contains_skill(
    text: str,
    skill: str,
) -> bool:
    pattern = re.compile(
        rf"(?<!\w){re.escape(skill)}(?!\w)",
        flags=re.IGNORECASE,
    )

    return bool(pattern.search(text))


def extract_skills(
    resume_text: str,
) -> tuple[list[str], list[str]]:
    detected = [
        skill
        for skill in SKILLS
        if contains_skill(
            resume_text,
            skill,
        )
    ]

    core = [skill for skill in detected if skill.lower() in CORE_SKILL_PRIORITY]

    secondary = [
        skill for skill in detected if skill.lower() not in CORE_SKILL_PRIORITY
    ]

    return core, secondary
