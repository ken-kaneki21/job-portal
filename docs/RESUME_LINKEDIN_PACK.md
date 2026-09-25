# Resume + LinkedIn Pack

## Resume bullets
- Built and deployed **Job Intelligence**, a production-grade job discovery and application-orchestration platform using Python, FastAPI, PostgreSQL/pgvector, Temporal, React, Docker and Railway; unified multi-source jobs into a normalized, deduplicated and provenance-aware dataset.
- Designed a hybrid ranking engine combining deterministic constraints, SentenceTransformer semantic similarity, structured JD-gap analysis, profile evidence and outcome feedback; production validation processed **965 active jobs** and persisted **490 ranked opportunities** in the first cloud run.
- Productized durable daily workflows with retries, data-quality checks, email digests, signed-session authentication, browser-assisted job capture and review-first Workday autofill; optimized semantic processing with batched embeddings and content-hash reuse.

## LinkedIn post draft
I wanted my next portfolio project to behave like a product, not a notebook or a demo.

So I built **Job Intelligence** — a private, production-deployed system that discovers jobs, normalizes and deduplicates them, understands my resume, ranks opportunities, prepares application assets, tracks outcomes, and keeps the workflow running with Temporal.

The stack: **Python, FastAPI, PostgreSQL + pgvector, Temporal, SentenceTransformers, React/Vite, Docker, Railway, CI/CD and Resend**.

A few things I cared about beyond “it works”:
- provenance and idempotency across multiple sources
- deterministic hard filters before AI scoring
- semantic + structured gap analysis rather than a single opaque score
- durable retries and data-quality checks
- review-first application assistance instead of blind auto-submit
- private authentication and a browser companion for user-assisted capture
- measurable production behavior: the first cloud run held 965 active canonical jobs and produced 490 ranked opportunities

The most useful engineering lesson was that productization exposes different problems than local development. The first cloud embedding pass became a real performance bottleneck, so I moved the system to batched inference and reuse of unchanged embeddings rather than scaling infrastructure blindly.

This is the kind of data/AI engineering work I enjoy: ingestion, modeling, orchestration, ML-aware systems, observability, reliability, and a usable product surface — end to end.
