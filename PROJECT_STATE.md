# Job Intelligence v2 — Project State

Last updated: 2026-09-21

## Purpose

Private, production-grade AI Job Intelligence and Application Orchestration platform for personal use and portfolio demonstration.

Primary goals:

- Fast job discovery
- Accurate candidate-job ranking
- Resume-driven personalization
- Privacy-first operation
- Reliable orchestration
- Explainable matching
- Application assistance
- Recruiter/company intelligence
- Production-quality engineering

---

# Current Branch

`v2`

Baseline:

- `v1.0.0`
- `v1.0.1`
- v2 branched from commit `ebd982d`

---

# Architecture

## Core stack

Backend:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector

Workflow orchestration:

- Temporal Python SDK

Data ingestion:

- API-first
- HTTPX
- BeautifulSoup where appropriate
- Playwright/browser-assisted workflows only where needed

Storage:

- PostgreSQL
- pgvector
- object storage planned for raw documents/assets

AI:

- deterministic rules
- semantic embeddings
- structured LLM outputs
- configurable LLM providers
- SentenceTransformers MiniLM embeddings

Frontend:

- React
- TypeScript
- Vite
- TanStack Query
- React Router
- Lucide icons
- custom CSS
- no Tailwind dependency

Observability:

- structured logs
- Prometheus
- Grafana
- Temporal UI

---

# Infrastructure

## PostgreSQL

Container:

`jobintel-postgres`

Image:

`pgvector/pgvector:pg17`

Host port:

`55432`

Migration head:

`98c205316bba`

---

## Temporal

Temporal address:

`localhost:7233`

Docker address:

`temporal:7233`

Namespace:

`default`

v2 task queue:

`job-intelligence-pipeline-v2`

Temporal UI:

`http://localhost:8080`

Current development preference:

Use the local Temporal worker during v2 profile development so locally generated profile files are available.

---

# Existing Job Sources

Implemented:

- Greenhouse
- Lever
- Ashby
- SmartRecruiters
- Adzuna

Future locked portal scope:

- LinkedIn
- Naukri
- Foundit
- Indeed

For portals without suitable public APIs, use legal/user-assisted import or browser-extension workflows rather than brittle credential scraping.

---

# Universal Candidate Profile

v2 moved away from a hardcoded `data_engineer` profile.

Implemented modules:

- `profile/universal.py`
- `profile/role_detection.py`
- `profile/adapter.py`
- `profile/runtime.py`
- `resume/parser.py`
- `resume/skills.py`
- `resume/service.py`
- `api_profile.py`

Current active profile:

`universal`

Current generated profile path:

`profiles/generated_v2.json`

Generated resume/profile files containing personal information must remain untracked.

Current target role families include:

- Data Engineer
- Senior Data Engineer
- Data Engineering
- Data Analyst
- Senior Data Analyst
- Business Data Analyst

Adjacent role families include:

- Analytics
- AI / GenAI
- Cloud
- Data Platform
- ML-related roles

Current preferred locations:

- Bengaluru
- Bangalore
- Hyderabad
- India

Important skills include:

- Python
- SQL
- Snowflake
- Airflow
- dbt
- AWS
- Azure
- LLM
- RAG

Current exclusions include:

- Director
- VP
- Principal
- Staff
- Architect
- Head of

Preferred maximum experience:

7 years

Hard maximum experience:

10 years

---

# Latest Validated Intelligence Run

Run:

`28`

Status:

successful

Jobs fetched:

`7477`

Active jobs:

`8210`

Relevant universal rankings:

`567`

Ranking buckets:

- High confidence: `1`
- Discovery: `466`
- Stretch: `100`

Known strong match:

Fam — Data Engineer (SDE 2)

Score:

`76.7`

---

# Ranking System

Implemented:

- deterministic hard filters
- semantic matching
- gap analysis
- bucket assignment
- persisted rankings
- profile-specific scoring

Buckets:

- high_confidence
- discovery
- stretch

Known future work:

- ranking threshold calibration
- labelled evaluation dataset
- learning-to-rank
- outcome feedback
- clearer score semantics
- better gap interpretation

---

# Current Important Backend Limitation

Broad-search discovery is still too Data-Engineering-centric.

Next backend priority:

Generate discovery queries dynamically from the universal candidate profile using:

- primary role families
- adjacent role families
- candidate skills
- preferred locations
- experience constraints

Avoid query explosion and unnecessary Adzuna/API usage.

---

# Profile Persistence Future State

Current development profile is file-based.

Production target:

Store active candidate profile in PostgreSQL, likely using versioned JSONB or structured relational/profile tables.

Generated JSON should become export/cache rather than source of truth.

---

# API / Frontend

API:

`http://127.0.0.1:8000`

Frontend:

`http://localhost:5173`

---

# Frontend Completed

## Overview

Connected to real backend data.

Displays:

- active jobs
- relevant jobs
- high-confidence count
- discovery count
- stretch context
- priority opportunities
- latest intelligence run
- next actions

---

## Discover

Connected to real rankings.

Implemented:

- all three ranking buckets
- search/filter
- job cards
- match score rings
- selected-job preview
- deep linking
- `/discover?job=<id>`
- URL-based selected job state
- selected-card scrolling
- skeleton loading

---

## Profile

Implemented:

- resume upload
- profile GET/PUT
- role intelligence
- detected skills
- geography
- profile editing
- active source resume information

---

## Motion / Interaction

Implemented:

- interactive surface hover
- card lift
- click feedback
- route transitions
- animated counters
- score rings
- skeleton shimmer
- reactive intelligence-network canvas
- random topology per load
- cursor interaction
- click impulse
- theme-aware network
- reduced-motion support
- hidden-tab canvas pause
- DPR cap
- mobile/touch safeguards

---

## Responsive Design

Implemented:

- desktop
- laptop
- tablet
- mobile
- compact sidebar
- mobile bottom navigation
- horizontal access to all nine navigation items
- compact mobile topbar
- light mode
- dark mode

---

## Command Palette

Implemented:

`Ctrl + K`

Capabilities:

- Overview
- Discover
- Applications
- Companies
- Outreach
- Profile
- Analytics
- Automations
- Settings
- Run Intelligence

Supports:

- keyboard search
- Arrow Up
- Arrow Down
- Enter
- Escape
- click-to-open from top search control

---

# Run Intelligence UI

Implemented robust state handling:

- idle
- starting
- running
- completed
- failed

Features:

- active workflow stored in localStorage
- restored after refresh
- Temporal status polling
- health endpoint fallback
- visibility/focus recheck
- wall-clock timeout
- query invalidation after completion

Do not launch full runs just for UI testing.

---

# Frontend Quality

Tailwind removed.

Frontend uses custom CSS.

Current quality commands:

```bash
npm run lint
npm run build

Latest state:

Both passing.

Backend Quality

Expected commands:

python -m ruff check .
python -m black --check .
python -m mypy src
python -m pytest -q

Previously validated before final frontend changes:

Ruff clean
Black clean
Mypy clean
134 tests passed

Re-run before v2 checkpoint commit.

Application Automation Scope

Application automation must remain user-controlled.

Planned Workday workflow:

detect application form
map known candidate profile fields
detect custom questions
generate or retrieve candidate-approved responses
autofill supported fields
visually highlight uncertain fields
require user review
user manually confirms/finalizes submission

Do not blindly auto-submit applications.

Locked Portal Scope

Future ingestion/import/application support should include:

LinkedIn
Naukri
Foundit
Indeed

Preferred hierarchy:

official API/feed where available
supported import/export
user-assisted browser extension
Playwright-assisted browser workflow only where appropriate

Avoid credential scraping and brittle automation.

Next Development Order
Immediate
Clean v2 git worktree
Run full backend/frontend quality suite
Commit v2 foundation checkpoint
Core v2 functionality
Make broad search universal-profile-driven
Add proper /rankings/stats endpoint
Persist active universal profile in PostgreSQL
Improve structured resume/profile extraction
Add ranking evaluation dataset and threshold calibration
Job portal expansion
LinkedIn
Naukri
Foundit
Indeed
Application assistance
Workday autofill
application question memory
candidate-approved answer library
application state tracking
Intelligence expansion
Company intelligence
recruiter discovery/outreach
application outcome tracking
learning-to-rank
analytics
scheduled/cloud execution
Privacy Rules

Never commit:

.env
API keys
passwords
generated resume/profile files containing personal information
raw private resumes
personal application answers unless explicitly intended

Generated candidate profile files must stay ignored.

Engineering Principles

Prefer:

small composable modules
deterministic logic where deterministic logic is sufficient
LLM only where semantic reasoning adds value
typed schemas
idempotency
retries/backoff
batching
caching
explicit lineage
observability
low resource usage
privacy
readable code
tests before large refactors

Avoid:

framework bloat
unnecessary abstractions
duplicate sources of truth
hidden automation
uncontrolled job submission
scraping that requires storing user credentials
