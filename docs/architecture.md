# Job Intelligence V2 Architecture

Job Intelligence V2 is a private, profile-driven job discovery, ranking,
application-assistance, tracking, and learning system.

## Data flow

1. Job sources and user-assisted portal imports create source records.
2. Canonical matching deduplicates jobs while retaining provenance.
3. Jobs move through normalized, enriched, gap-analysis, and ranking stages.
4. Ranking combines deterministic fit, semantic similarity, gap evidence,
   profile evidence, and bounded historical-outcome feedback.
5. The frontend exposes discovery and application workflows.
6. Application transitions are written to immutable event history.
7. Completed outcomes feed learning and offline evaluation.

## Core components

- Python / FastAPI
- PostgreSQL + pgvector
- Temporal workflows
- deterministic and embedding-based ranking
- optional LLM enrichment
- React / TypeScript frontend
- Playwright review-first Workday assistance
- structured observability
- Docker-based infrastructure

## Privacy and safety

Candidate profiles remain private runtime data. `.env`, generated candidate
profiles, credentials, and secrets must not be committed.

Portal ingestion is user-assisted and does not scrape credentials.

Workday assistance never clicks the final Submit button.
