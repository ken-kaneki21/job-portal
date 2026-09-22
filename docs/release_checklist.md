# V2 Release Checklist

## Repository

- [ ] Working tree is clean.
- [ ] `.env` is not tracked.
- [ ] Candidate profile JSON files are not tracked.
- [ ] No temporary repair/context scripts are tracked.
- [ ] Pre-commit passes.

## Backend

- [ ] Ruff lint passes.
- [ ] Black passes.
- [ ] Mypy passes.
- [ ] Full pytest suite passes.
- [ ] `pip check` passes.
- [ ] Alembic current equals Alembic head.
- [ ] `/health` returns healthy.
- [ ] `/ready` returns ready.
- [ ] `/version` reports the intended release candidate.

## Frontend

- [ ] ESLint passes.
- [ ] TypeScript/Vite production build passes.
- [ ] Applications UI uses real backend data.

## Infrastructure

- [ ] Docker Compose validates.
- [ ] PostgreSQL + pgvector are healthy.
- [ ] Temporal is reachable when required.

## Job workflow

- [ ] Portal imports validate before persistence.
- [ ] Workday helper remains review-first.
- [ ] Final Submit is never automated.
- [ ] Status transitions create immutable history.
- [ ] Outcome learning remains bounded.
- [ ] Offline evaluation handles empty history safely.

## Release

- [ ] `python -m jobintel.release_check` passes.
- [ ] Final smoke test succeeds.
- [ ] Release commit is created.
- [ ] Tag `v2.0.0` only after final verification.
