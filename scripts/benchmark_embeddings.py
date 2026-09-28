from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "eval" / "embedding_benchmark.json"
OUTPUT = ROOT / "artifacts" / "embedding_benchmarks" / "results.json"


def main():
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    texts = [payload["profile"], *payload["jobs"]]
    from jobintel.semantic.embeddings import clear_embedding_caches, embed_texts

    results, reference = [], None
    for backend in ["torch", "onnx-fp32", "onnx-int8"]:
        os.environ["JOBINTEL_EMBEDDING_BACKEND"] = backend
        for batch_size in [1, 8, 16, 32, 64, 128]:
            clear_embedding_caches()
            process = psutil.Process()
            rss_before = process.memory_info().rss
            start = time.perf_counter()
            vectors = embed_texts(texts, batch_size=batch_size)
            cold_ms = (time.perf_counter() - start) * 1000
            timings, peak = [], process.memory_info().rss
            for _ in range(5):
                start = time.perf_counter()
                vectors = embed_texts(texts, batch_size=batch_size)
                timings.append((time.perf_counter() - start) * 1000)
                peak = max(peak, process.memory_info().rss)
            p50 = statistics.median(timings)
            row = {
                "backend": backend,
                "batch_size": batch_size,
                "cold_start_ms": round(cold_ms, 3),
                "p50_ms": round(p50, 3),
                "p95_ms": round(float(np.percentile(timings, 95)), 3),
                "throughput_items_per_sec": round(len(texts) / (p50 / 1000), 3),
                "rss_delta_mb": round((peak - rss_before) / 1024 / 1024, 3),
            }
            if batch_size == 32:
                if backend == "torch":
                    reference = vectors.copy()
                else:
                    cosine = np.sum(reference * vectors, axis=1)
                    ref_scores, scores = (
                        reference[1:] @ reference[0],
                        vectors[1:] @ vectors[0],
                    )
                    ref_rank, rank = np.argsort(-ref_scores), np.argsort(-scores)
                    for k in (10, 20):
                        kk = min(k, len(rank))
                        row[f"top{k}_overlap"] = round(
                            len(set(ref_rank[:kk]) & set(rank[:kk])) / kk, 4
                        )
                    row["mean_embedding_cosine"] = round(float(cosine.mean()), 8)
                    row["min_embedding_cosine"] = round(float(cosine.min()), 8)
                    row["max_abs_score_delta"] = round(
                        float(np.max(np.abs(ref_scores - scores))), 8
                    )
            results.append(row)
            print(json.dumps(row))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({"model": "all-MiniLM-L6-v2", "results": results}, indent=2),
        encoding="utf-8",
    )
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
