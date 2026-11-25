# Job Intelligence review candidate

The source checkpoint is `3d3c02b`. The accepted synthetic cached integration report records application commit `230d817` plus the runner correction at `3d3c02b`. The earlier managed Docker failure remains in the acceptance runbook.

On a Windows host with the cached MiniLM model and existing Docker images:

```powershell
pwsh -NoProfile -File scripts/verify-cached-stack.ps1 -Python (Get-Command python).Source -OutputDirectory (Join-Path $PWD ('local/job-cache-' + (Get-Date -Format yyyyMMdd-HHmmss)))
```

The adapter ingests cached source records, PostgreSQL/pgvector stores normalized data, Temporal replays a workflow after a controlled worker restart and FastAPI exposes results with session authentication. The run covers one login and one controlled interruption between activities. The same two raw records and single eligible rank persisted. Live-source ingestion and cross-account isolation have separate coverage requirements. [Accepted runtime report](evidence/sprint-cached-acceptance.json).

The companion sprint uses the checked-in ranker and compares deterministic, BM25, MiniLM and 50/50 hybrid ranking over 15 holdout postings and three authored intents. Dense and hybrid gain 0.013 nDCG@5 over the incumbent, below the preset 0.02 threshold. Keep the incumbent. Use the companion's `experiments/retrieval.py` and frozen fixture. [Retrieval results](evidence/sprint-retrieval-result.json).

Dependencies and local assets include PostgreSQL, pgvector, Temporal, and the cached Sentence Transformers all-MiniLM-L6-v2 encoder. Encoder weights are not included in this review delta. Confirm the code and asset licence scope before publication.
