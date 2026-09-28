from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
SUPPORTED_BACKENDS = {"torch", "onnx-fp32", "onnx-int8"}


def get_backend() -> str:
    backend = os.getenv("JOBINTEL_EMBEDDING_BACKEND", "torch").strip().lower()
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported JOBINTEL_EMBEDDING_BACKEND={backend!r}")
    return backend


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME, device="cpu")


def clear_embedding_caches() -> None:
    get_model.cache_clear()
    try:
        from jobintel.semantic.onnx_runtime import clear_caches

        clear_caches()
    except ImportError:
        pass


def embed_text(text: str) -> np.ndarray:
    return embed_texts([text], batch_size=1)[0]


def embed_texts(texts: list[str], *, batch_size: int = 32) -> np.ndarray:
    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
    backend = get_backend()
    if backend == "torch":
        result = get_model().encode(
            texts,
            batch_size=max(1, batch_size),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(result, dtype=np.float32)
    from jobintel.semantic.onnx_runtime import embed_texts_onnx

    return embed_texts_onnx(
        texts,
        batch_size=batch_size,
        precision="fp32" if backend == "onnx-fp32" else "int8",
    )


def cosine_similarity(left, right) -> float:
    left_array, right_array = np.asarray(left, dtype=np.float32), np.asarray(
        right, dtype=np.float32
    )
    if left_array.size == 0 or right_array.size == 0:
        return 0.0
    left_norm, right_norm = np.linalg.norm(left_array), np.linalg.norm(right_array)
    if left_norm == 0 or right_norm == 0:
        return 0.0
    similarity = float(np.dot(left_array, right_array) / (left_norm * right_norm))
    return max(0.0, min(1.0, similarity))
