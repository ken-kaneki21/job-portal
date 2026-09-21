from __future__ import annotations

import re
from collections import defaultdict

from jobintel.profile.universal import (
    RoleFamily,
    RolePriority,
)

ROLE_SIGNALS: dict[str, tuple[str, ...]] = {
    "Data Engineer": (
        "data engineer",
        "etl",
        "elt",
        "airflow",
        "dbt",
        "spark",
        "pyspark",
        "snowflake",
        "databricks",
        "data pipeline",
        "data warehouse",
        "azure data factory",
        "adf",
    ),
    "Analytics Engineer": (
        "analytics engineer",
        "dbt",
        "data modeling",
        "dimensional modeling",
        "snowflake",
        "sql",
        "semantic layer",
        "data warehouse",
    ),
    "Data Analyst": (
        "data analyst",
        "analytics",
        "power bi",
        "tableau",
        "dashboard",
        "reporting",
        "sql",
        "business intelligence",
    ),
    "AI Engineer": (
        "ai engineer",
        "llm",
        "large language model",
        "openai",
        "rag",
        "retrieval augmented generation",
        "agent",
        "prompt engineering",
        "embeddings",
        "vector database",
    ),
    "GenAI Engineer": (
        "generative ai",
        "genai",
        "llm",
        "rag",
        "prompt engineering",
        "agents",
        "openai",
        "groq",
        "vector database",
        "embeddings",
    ),
    "ML Engineer": (
        "machine learning",
        "ml engineer",
        "model deployment",
        "feature engineering",
        "mlflow",
        "scikit-learn",
        "tensorflow",
        "pytorch",
    ),
    "Data Platform Engineer": (
        "data platform",
        "platform engineer",
        "spark",
        "kafka",
        "snowflake",
        "databricks",
        "airflow",
        "data infrastructure",
    ),
    "Cloud Data Engineer": (
        "azure",
        "aws",
        "gcp",
        "cloud data",
        "data factory",
        "databricks",
        "snowflake",
        "s3",
        "bigquery",
    ),
}


def normalize_text(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        value.lower(),
    ).strip()


def detect_role_families(
    resume_text: str,
) -> list[RoleFamily]:
    normalized = normalize_text(
        resume_text,
    )

    role_scores: dict[str, float] = defaultdict(float)
    role_signals: dict[str, list[str]] = defaultdict(list)

    for role_name, signals in ROLE_SIGNALS.items():
        for signal in signals:
            occurrences = normalized.count(
                signal.lower(),
            )

            if occurrences <= 0:
                continue

            role_scores[role_name] += min(
                occurrences,
                3,
            )

            role_signals[role_name].append(
                signal,
            )

    if not role_scores:
        return []

    max_score = max(
        role_scores.values(),
    )

    results: list[RoleFamily] = []

    for role_name, raw_score in role_scores.items():
        confidence = min(
            raw_score
            / max(
                max_score,
                1.0,
            ),
            1.0,
        )

        priority: RolePriority

        if confidence >= 0.75:
            priority = "primary"
        elif confidence >= 0.45:
            priority = "secondary"
        else:
            priority = "discovery"

        results.append(
            RoleFamily(
                name=role_name,
                confidence=round(
                    confidence,
                    4,
                ),
                priority=priority,
                enabled=True,
                matched_signals=sorted(
                    set(
                        role_signals[role_name],
                    ),
                ),
            ),
        )

    return sorted(
        results,
        key=lambda item: item.confidence,
        reverse=True,
    )
