from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(
    text: str,
) -> np.ndarray:
    model = get_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return np.asarray(
        embedding,
        dtype=np.float32,
    )


def embed_texts(
    texts: list[str],
    *,
    batch_size: int = 32,
) -> np.ndarray:
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=max(1, batch_size),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype=np.float32)


def cosine_similarity(
    left,
    right,
) -> float:
    left_array = np.asarray(
        left,
        dtype=np.float32,
    )

    right_array = np.asarray(
        right,
        dtype=np.float32,
    )

    if left_array.size == 0 or right_array.size == 0:
        return 0.0

    left_norm = np.linalg.norm(left_array)

    right_norm = np.linalg.norm(right_array)

    if left_norm == 0 or right_norm == 0:
        return 0.0

    similarity = float(
        np.dot(
            left_array,
            right_array,
        )
        / (left_norm * right_norm)
    )

    return max(
        0.0,
        min(
            1.0,
            similarity,
        ),
    )
