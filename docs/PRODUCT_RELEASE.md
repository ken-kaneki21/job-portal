# Job Intelligence — Production Product Release

A private, production-deployed job discovery and application-orchestration product.

## Product capabilities
- Adzuna broad discovery plus direct Greenhouse, Lever, Ashby and SmartRecruiters connectors.
- Progressive ATS discovery from companies found during broad search.
- Browser companion for user-assisted LinkedIn, Naukri, Foundit, Indeed and generic job-page capture.
- CSV/JSON portal import with provenance, normalization and deduplication.
- Universal resume/profile understanding.
- Deterministic hard filters + SentenceTransformer semantic similarity + structured JD-gap analysis + profile evidence + outcome feedback.
- Durable Temporal orchestration with retries, idempotency patterns and data-quality checks.
- PostgreSQL + pgvector persistence.
- Application assets, tracker/history, and review-first Workday assistance.
- Automatic daily runs and ranked email digests.
- Signed HttpOnly sessions, login throttling, separate companion token, CORS controls, and private profile handling.
- Batched semantic inference plus content-hash reuse.
- React product UI: Overview, Discover, Applications, Companies, Outreach, Integrations, Profile, Analytics, Automations and Settings.

## Safety boundary
The product deliberately stops before final job application submission. It assists with preparation/autofill, but final review and Submit stay with the user.

## Production validation already observed
The first cloud run held 965 active canonical jobs and persisted 490 eligible rankings. The original first-pass embedding stage dominated runtime; this release batches inference and continues to skip unchanged embeddings by content hash.

## Architecture
React/Vite → FastAPI → PostgreSQL/pgvector
                         ↘ Temporal → Python worker
                                      ↘ Job/ATS APIs
                                      ↘ SentenceTransformers
                                      ↘ Resend

No additional Railway service is required by this release.
