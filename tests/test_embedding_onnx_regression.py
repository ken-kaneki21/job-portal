import json
import os
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("JOBINTEL_RUN_ONNX_TESTS") != "1",
    reason="Set JOBINTEL_RUN_ONNX_TESTS=1",
)
CORPUS = Path(__file__).resolve().parents[1] / "eval" / "embedding_benchmark.json"


def embed(monkeypatch, backend, texts):
    monkeypatch.setenv("JOBINTEL_EMBEDDING_BACKEND", backend)
    from jobintel.semantic.embeddings import clear_embedding_caches, embed_texts

    clear_embedding_caches()
    return embed_texts(texts, batch_size=32)


@pytest.mark.parametrize(
    ("backend", "min_cosine", "min_overlap"),
    [("onnx-fp32", 0.995, 0.9)],
)
def test_embedding_and_ranking_regression(
    monkeypatch, backend, min_cosine, min_overlap
):
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    texts = [payload["profile"], *payload["jobs"]]
    reference, candidate = embed(monkeypatch, "torch", texts), embed(
        monkeypatch, backend, texts
    )
    assert reference.shape == candidate.shape
    assert candidate.shape[1] == 384
    assert np.isfinite(candidate).all()
    assert np.allclose(np.linalg.norm(candidate, axis=1), 1.0, atol=1e-5)
    assert float(np.sum(reference * candidate, axis=1).min()) >= min_cosine
    ref_scores, scores = reference[1:] @ reference[0], candidate[1:] @ candidate[0]
    ref_rank, rank = np.argsort(-ref_scores), np.argsort(-scores)
    k = min(10, len(rank))
    overlap = len(set(ref_rank[:k]) & set(rank[:k])) / k
    assert overlap >= min_overlap
