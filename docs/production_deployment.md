# Production Deployment

## Preconditions

- PostgreSQL with pgvector is available.
- Alembic migrations are at head.
- Candidate profile exists in the database.
- Temporal is reachable when pipeline execution is required.
- Runtime secrets are supplied through environment variables.
- `.env` and generated candidate profile JSON files remain untracked.

## Release gate

```bat
python -m jobintel.release_check
```

## Backend validation

```bat
pre-commit run --all-files
python -m pytest -q
```

## Frontend validation

```bat
cd frontend
npm run lint
npm run build
```

## Runtime endpoints

- `GET /health`
- `GET /ready`
- `GET /version`

## Safety boundary

Do not enable blind application submission. Workday automation must stop for
manual review before final submission.
