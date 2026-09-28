import numpy as np
import pytest

from jobintel.semantic import embeddings


def test_default_backend_is_torch(monkeypatch):
    monkeypatch.delenv("JOBINTEL_EMBEDDING_BACKEND", raising=False)
    assert embeddings.get_backend() == "torch"


@pytest.mark.parametrize("backend", ["torch", "onnx-fp32", "onnx-int8"])
def test_supported_backends(monkeypatch, backend):
    monkeypatch.setenv("JOBINTEL_EMBEDDING_BACKEND", backend)
    assert embeddings.get_backend() == backend


def test_invalid_backend(monkeypatch):
    monkeypatch.setenv("JOBINTEL_EMBEDDING_BACKEND", "invalid")
    with pytest.raises(ValueError):
        embeddings.get_backend()


def test_empty_batch():
    result = embeddings.embed_texts([])
    assert result.shape == (0, 384)
    assert result.dtype == np.float32
