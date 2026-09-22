# Application Operations

This layer turns the ranking system into a practical day-to-day application workflow.

## Quick status capture

```bat
python -m jobintel.application_capture --job-id 123 --status applied
python -m jobintel.application_capture --job-id 123 --status interviewing --notes "Recruiter screen scheduled"
python -m jobintel.application_capture --job-id 123 --status rejected
python -m jobintel.application_capture --job-id 123 --status offer
python -m jobintel.application_capture --job-id 123 --history
```

Canonical statuses:

- new
- seen
- saved
- dismissed
- applied
- interviewing
- rejected
- offer

Legacy aliases are normalized:

- reviewed -> seen
- skipped -> dismissed
- interview -> interviewing

## API

- `GET /application-ops/summary`
- `GET /application-ops/jobs/{job_id}/answers`
- `GET /application-ops/jobs/{job_id}/readiness`
- `GET /application-ops/jobs/{job_id}/workday-assist`
- `POST /application-ops/jobs/{job_id}/status`
- `GET /application-ops/jobs/{job_id}/history`

Example status payload:

```json
{
  "status": "applied",
  "notes": "Applied through company careers site."
}
```

## Review model

Application answers are generated deterministically from the universal profile when possible.

Sensitive or decision-sensitive fields remain reviewable.

The Workday assist endpoint is intentionally review-first and never authorizes blind final submission.

## Outcome learning

Interviewing, rejected, and offer states create completed outcome data that can feed the existing outcome-learning and offline evaluation layers.
