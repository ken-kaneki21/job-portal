from sqlalchemy import select

from jobintel.db.models import (
    JobEmbeddingRecord,
)
from jobintel.semantic.embeddings import (
    MODEL_NAME,
    cosine_similarity,
)


def load_job_embedding(
    session,
    job_id: int,
):
    record = session.scalar(
        select(JobEmbeddingRecord)
        .where(JobEmbeddingRecord.job_id == job_id)
        .where(JobEmbeddingRecord.model_name == MODEL_NAME)
    )

    if record is None:
        return None

    return record.embedding


def score_semantic_similarity(
    *,
    profile_embedding,
    job_embedding,
) -> float:
    if job_embedding is None:
        return 0.0

    similarity = cosine_similarity(
        profile_embedding,
        job_embedding,
    )

    # Convert 0..1 cosine similarity
    # into a 0..10 ranking contribution.
    return round(
        similarity * 10.0,
        2,
    )
