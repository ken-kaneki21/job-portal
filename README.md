# Job Intelligence

Production-grade AI job discovery, ranking and application orchestration platform.

Job Intelligence turns fragmented job searching into a durable data and AI
pipeline: discover opportunities → normalize and deduplicate → enrich →
embed → rank against a candidate profile → analyze gaps → prepare application
assets → track outcomes.

## Product

<img width="1904" height="909" alt="image" src="https://github.com/user-attachments/assets/1e47f8f6-2578-4f12-9b90-f6e1f1cd75a6" />



### What it does

- Multi-source ATS/API job discovery
- Canonical deduplication and provenance tracking
- Candidate-profile-aware ranking
- Deterministic eligibility + semantic similarity
- Sentence Transformer embeddings with pgvector
- JD enrichment and skill-gap analysis
- Explainable opportunity scoring
- Application tracking and outreach assets
- LinkedIn/Naukri/Foundit/Indeed structured imports
- Browser-assisted job capture
- Review-first Workday assistance
- Durable Temporal orchestration
- Scheduled intelligence runs and email delivery
- Authenticated production dashboard

## Product walkthrough

### Discover and rank opportunities

<img width="1903" height="909" alt="image" src="https://github.com/user-attachments/assets/28d5afe8-ca13-4528-9e86-3627749ce8d3" />


Each opportunity is evaluated using deterministic eligibility signals,
semantic similarity and candidate-profile evidence. Rankings retain their
pipeline-run provenance and expose the signals used to prioritize the job.

### Profile intelligence

<img width="1904" height="906" alt="image" src="https://github.com/user-attachments/assets/0d6d8497-64eb-4eab-bda4-e3c0de3a1c29" />


The resume is transformed into a structured candidate profile containing
role families, skills, experience and geographic preferences. The same
profile drives discovery, ranking, gap analysis and application assistance.

### Integrations and application assistance

<img width="1907" height="911" alt="image" src="https://github.com/user-attachments/assets/a3d0f3d9-6831-437f-b521-022d71764416" />


The platform supports structured portal imports and browser-assisted capture
rather than credential scraping. Workday assistance remains review-first and
never performs the final submission automatically.

## Production snapshot

Latest validated production run:

- 1,215 active jobs
- 596 profile-relevant opportunities
- 526 discovery opportunities
- 70 stretch opportunities
- Durable Temporal pipeline execution
- Scheduled email delivery verified
- 214 automated tests passing
- Authenticated production access
- CI/CD quality gates passing

> Counts are a point-in-time production snapshot and change as new jobs are
> discovered and old opportunities expire.

## Architecture

<img width="3878" height="3986" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/82f6a0f1-8e8b-4c5c-a5eb-a4784b071b13" />


## How ranking works

Candidate Profile
        ↓
Hard Eligibility Filters
        ↓
Deterministic Match Signals
        ↓
Semantic Embeddings / pgvector
        ↓
JD Gap Analysis
        ↓
Opportunity Classification
        ↓
High Confidence / Discovery / Stretch

## Pipeline

Temporal orchestrates:

1. source ingestion
2. normalization
3. canonical deduplication
4. persistence and lifecycle updates
5. JD enrichment
6. batched embedding generation
7. profile-aware ranking
8. gap analysis
9. application asset generation
10. notification delivery
11. pipeline finalization

## Engineering decisions

### Deterministic before generative AI
Rules are used where correctness can be expressed deterministically.
LLMs are reserved for tasks where semantic reasoning adds value.

### Provenance first
Every job retains its source identity, timestamps, canonical mapping and
pipeline history.

### Durable execution
Temporal provides retries, recovery, workflow history and activity isolation.

### Privacy and application safety
Secrets remain outside source control. Authentication protects the production
workspace. Portal ingestion does not require credential scraping, and
application automation remains review-first.

## Technology

Backend:
Python · FastAPI · SQLAlchemy · PostgreSQL · pgvector · Alembic

AI:
Sentence Transformers · PyTorch · OpenAI · Groq · embeddings

Orchestration:
Temporal

Frontend:
React · TypeScript · Vite

Infrastructure:
Docker · Railway · GitHub Actions

Quality:
Pytest · Ruff · Black · Mypy · pre-commit

Notifications:
Resend

## Quality

214 automated tests passing

Quality gates:
- Ruff
- Black
- Mypy
- Pytest
- ESLint
- TypeScript production build
- pre-commit
- GitHub Actions

## Running Locally

### Prerequisites

Before starting, install:

- Python 3.11+
- Node.js 20+
- Docker Desktop
- Git

The application uses PostgreSQL with `pgvector` for persistence and Temporal
for durable workflow orchestration.

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd job-intelligence
```

### 2. Create the Python environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Configure environment variables

Copy the example environment file.

Windows:

```bash
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Update `.env` with the services you want to enable.

At minimum, configure the database and Temporal connection required by your
local environment.

Optional integrations such as job-source APIs, AI providers and email
notifications require their corresponding credentials.

> Never commit `.env`, API keys, database credentials, authentication secrets,
> browser-companion tokens or production configuration files.

### 4. Start infrastructure

Start the local infrastructure defined by Docker Compose:

```bash
docker compose up -d
```

Check that the containers are running:

```bash
docker compose ps
```

This provides the local infrastructure required by the application, including
PostgreSQL/pgvector and Temporal where configured by the repository.

### 5. Apply database migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
uvicorn jobintel.api:app --reload
```

Verify the API:

```text
http://127.0.0.1:8000/health
```

### 7. Start the Temporal worker

Open another terminal, activate the same Python environment, and run the
worker command configured by the project.

The worker executes the durable pipeline activities used for discovery,
normalization, enrichment, embeddings, ranking, gap analysis and
notifications.

### 8. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server will print the local frontend URL.

If required, configure the frontend API base URL in:

```text
frontend/.env.local
```

For example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

`frontend/.env.local` is local configuration and should not be committed.

### 9. Run the quality gates

Backend:

```bash
python -m ruff check src tests
python -m black --check src tests
python -m mypy src
python -m pytest -q
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
cd ..
```

Full repository checks:

```bash
pre-commit run --all-files
```

The `v2.1.0` release was validated with **214 automated tests passing** in
addition to the frontend and repository quality gates.

---

## Security & Privacy

Job Intelligence is designed as a private, user-controlled workspace.
Security boundaries are intentionally part of the product architecture rather
than being added only at the UI layer.

### Authentication

Production API routes are protected by authenticated sessions.

The application uses:

- signed session tokens
- `HttpOnly` session cookies
- secure-cookie support for production
- configurable session expiration
- login throttling
- protected API routes
- credential-aware frontend requests

Public health checks and authentication entry points are kept separate from
protected application data.

Authentication credentials and session secrets are supplied through
environment variables and are never intended to be stored in source control.

### Secret Management

Secrets must be provided through local environment files or the deployment
platform's secret-management system.

Examples include:

- database credentials
- API keys
- AI-provider credentials
- email-provider credentials
- authentication secrets
- browser-companion tokens

The repository intentionally ignores local and production secret files such as:

```text
.env
frontend/.env.local
railway_api_final_variables.txt
railway_worker_final_variables.txt
profile_b64.txt
```

`.env.example` documents configuration names only and must contain placeholders,
not real credentials.

### Candidate Data

Resume and candidate-profile information can contain personal information.

Generated or user-specific profile data should therefore remain outside public
source control. Only schemas, parsers, examples containing synthetic data and
the application logic required to process profiles should be committed.

Do not commit:

- personal resumes unless intentionally published
- generated candidate profiles
- private contact information
- application credentials
- exported job-board account data containing sensitive information

### Browser Companion

The browser companion uses a dedicated companion token rather than the user's
application login password.

Its purpose is to assist with user-controlled capture and application
workflows. It is not designed to collect job-board passwords.

Companion tokens should be treated as secrets and supplied through private
configuration only.

### Portal Integrations

LinkedIn, Naukri, Foundit and Indeed support is designed around structured
user-provided imports and browser-assisted capture.

The system does **not** require storing portal passwords or implementing
credential-based account scraping.

This preserves a clear boundary between job intelligence and account
automation.

### Application Safety

Application assistance is deliberately **review-first**.

The system can help with:

- reusable profile answers
- field mapping
- resume selection/upload workflows
- required-field detection
- application preparation

Sensitive or consequential fields remain reviewable by the user.

Most importantly:

> **The system does not perform the final application submission automatically.**

The user reviews the browser state and makes the final submission decision.

### Production Isolation

Production services are configured separately from local development.

Deployment credentials, database URLs, session secrets, notification keys and
other production configuration are managed outside the Git repository.

The public repository should contain application code and documentation—not a
copy of the production environment.

### Responsible Use

This project is intended for personal job-search intelligence, portfolio
demonstration and engineering experimentation.

Users deploying their own instance are responsible for complying with the
terms, access policies and automation restrictions of any external services
they connect to.

## Release

Current production release: **v3.0.0**

## Product completion

JobLens is feature-complete as a personal job-intelligence platform. The final architecture closes the loop between ranked recommendations, application outcomes and measurable ranking quality, while pipeline-run quality snapshots make freshness and coverage visible. Future work is intentionally limited to bug fixes, source maintenance, dependency/security updates and improvements justified by real usage.

The ranking evaluation layer reports Precision@K, Recall@K, lift, pairwise accuracy, NDCG@K and MRR from historically valid application outcomes. Outcome-derived adjustments activate only after sufficient evidence accumulates; sparse data remains neutral. Pipeline runs persist quality snapshots covering scan failures, freshness, embedding coverage and ranking coverage.

## License

Personal and portfolio use.

## Embedding inference optimization

JobLens supports the reference PyTorch embedding path plus ONNX Runtime FP32 and dynamically quantized INT8 CPU inference for `all-MiniLM-L6-v2`. PyTorch remains the default backend. The benchmark uses sanitized job/profile text and measures cold-start and p50/p95 latency, throughput, embedding cosine consistency, ranking overlap and score deltas across batch sizes 1, 8, 16, 32, 64 and 128. Generated ONNX models and benchmark output stay under the ignored `artifacts/` directory. Performance numbers are reported only from measured runs.

On the local CPU benchmark at batch size 32, ONNX Runtime FP32 reduced median embedding latency from 52.84 ms to 33.05 ms (~37%) and increased throughput from 473 to 756 items/s (~60%) versus the PyTorch baseline. Embedding parity remained effectively exact (minimum cosine similarity 0.99999988) with 100% Top-10 and Top-20 ranking overlap. Dynamic INT8 reached 1,034 items/s but was not promoted because minimum embedding cosine fell to 0.94595 and Top-10 overlap to 90%.
