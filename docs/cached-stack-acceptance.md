# Cached Job Intelligence stack acceptance

The acceptance harness uses the existing PostgreSQL/pgvector and Temporal
Compose services with project-scoped names and volumes. The evaluated job
content is synthetic and loaded through the actual Greenhouse adapter using
a cached HTTP response. Ingestion, sync, ranking, database writes and signed
session HTTP routes are application code. This focused Temporal workflow uses
real Temporal and two distinct worker processes. It replays the same ingestion
and ranking work after a durable checkpoint. Its interruption is between
activities. Full production scheduling and in-flight activity interruption
have separate coverage requirements.

## Run on a Windows host with Docker Desktop

Use the existing Python environment and cached MiniLM model. The three
base Compose images must already be present locally. Choose a fresh evidence
folder for each run.

```powershell
pwsh -NoProfile -File scripts/verify-cached-stack.ps1 -Python <venv-python.exe> -OutputDirectory <new-evidence-directory> -PreflightOnly
pwsh -NoProfile -File scripts/verify-cached-stack.ps1 -Python <venv-python.exe> -OutputDirectory <different-evidence-directory>
```

The runner forbids pulls and builds, binds disposable ports to loopback,
applies Alembic to its new PostgreSQL database, then starts a native Uvicorn
process. After the first activity commits, it kills the first worker, starts a
second, signals the existing workflow and compares the persisted result after
replay. It stops only its own services and retains project volumes for review.

Expected corpus state: two job rows, two raw rows after replay, numeric
floors 5 and 2, and the second job alone in the ranking for the cap of 4.
Expected HTTP results: anonymous rankings return 401, valid sign-in sees the
persisted row, and an unpopulated named profile has zero ranked rows. Profile
names filter data under the single-account login. The test makes no claim about
authorization between distinct account identities.

Outputs: gate.json, worker.log, temporal-postgres.json, and accepted.json
after the HTTP assertion passes. Exit 0 indicates the requested mode passed.
Exit 2 indicates an unmet prerequisite. Exit 1 indicates execution failed
after starting the stack.

## Current verification

24 November 2026: static Compose isolation validation passed. Alembic rendered
PostgreSQL SQL through revision `d1f0a4c92b31` offline. Runtime acceptance
stopped at the missing Docker Desktop Linux engine pipe. The WSL query returned
`E_ACCESSDENIED`. No online migration, authenticated ranking, or Temporal
recovery result was observed.
