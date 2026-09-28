from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
DEFAULT_MODEL_DIR = Path("artifacts/embedding_models/all-MiniLM-L6-v2")


def model_dir() -> Path:
    return Path(os.getenv("JOBINTEL_ONNX_MODEL_DIR", str(DEFAULT_MODEL_DIR)))


def fp32_path() -> Path:
    return model_dir() / "model.onnx"


def int8_path() -> Path:
    return model_dir() / "model.int8.onnx"


def mean_pool(hidden: np.ndarray, mask: np.ndarray) -> np.ndarray:
    expanded = np.expand_dims(mask.astype(np.float32), -1)
    return np.sum(hidden * expanded, axis=1) / np.clip(
        np.sum(expanded, axis=1), 1e-9, None
    )


def normalize(vectors: np.ndarray) -> np.ndarray:
    vectors = np.asarray(vectors, dtype=np.float32)
    return vectors / np.clip(
        np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12, None
    )


def export_fp32(force: bool = False) -> Path:
    target = fp32_path()
    if target.exists() and not force:
        return target
    import torch
    from sentence_transformers import SentenceTransformer

    target.parent.mkdir(parents=True, exist_ok=True)
    sentence_model = SentenceTransformer(MODEL_NAME, device="cpu")
    transformer = sentence_model[0].auto_model
    transformer.eval()  # type: ignore[union-attr]
    sample = sentence_model.tokenizer(
        ["Job intelligence ONNX export sample"],
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )

    class Encoder(torch.nn.Module):
        def __init__(self, wrapped):
            super().__init__()
            self.wrapped = wrapped

        def forward(self, input_ids, attention_mask):
            return self.wrapped(
                input_ids=input_ids, attention_mask=attention_mask, return_dict=False
            )[0]

    torch.onnx.export(
        Encoder(transformer),
        (sample["input_ids"], sample["attention_mask"]),
        str(target),
        input_names=["input_ids", "attention_mask"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "last_hidden_state": {0: "batch", 1: "sequence"},
        },
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )
    return target


def export_int8(force: bool = False) -> Path:
    target = int8_path()
    if target.exists() and not force:
        return target
    from onnxruntime.quantization import (
        QuantType,
        quantize_dynamic,
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    quantize_dynamic(str(export_fp32()), str(target), weight_type=QuantType.QInt8)
    return target


@lru_cache(maxsize=1)
def tokenizer():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME, device="cpu").tokenizer


@lru_cache(maxsize=2)
def session(precision: str):
    import onnxruntime as ort

    if precision == "fp32":
        path = export_fp32()
    elif precision == "int8":
        path = export_int8()
    else:
        raise ValueError(f"Unsupported ONNX precision: {precision}")
    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(
        str(path), sess_options=options, providers=["CPUExecutionProvider"]
    )


def clear_caches() -> None:
    tokenizer.cache_clear()
    session.cache_clear()


def embed_texts_onnx(
    texts: list[str], *, batch_size: int = 32, precision: str = "fp32"
) -> np.ndarray:
    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
    tok, ort_session, chunks = tokenizer(), session(precision), []
    size = max(1, batch_size)
    for start in range(0, len(texts), size):
        encoded = tok(
            texts[start : start + size],
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="np",
        )
        feeds = {
            "input_ids": np.asarray(encoded["input_ids"], dtype=np.int64),
            "attention_mask": np.asarray(encoded["attention_mask"], dtype=np.int64),
        }
        hidden = ort_session.run(["last_hidden_state"], feeds)[0]
        chunks.append(normalize(mean_pool(hidden, feeds["attention_mask"])))
    vectors = np.concatenate(chunks).astype(np.float32, copy=False)
    if vectors.shape[1] != EMBEDDING_DIMENSION:
        raise RuntimeError(f"Expected 384 dimensions, got {vectors.shape[1]}")
    return vectors
