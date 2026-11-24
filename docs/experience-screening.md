# Experience screening

This check helps a candidate distinguish required tenure from preferred
qualifications. The ranking entry point uses the strongest recognized mandatory
floor. A lower skill or headline number cannot erase an explicit higher floor.
Passing the global floor leaves individual skills and tenure for review.

## Cached demo

Use the repository's Python 3.13+ development environment. From the root, run
these PowerShell commands with no production configuration:

```powershell
$env:PYTHONPATH = 'src'
$env:DATABASE_URL = 'sqlite://'
python scripts/evaluate_experience_screening.py --out out/screening-demo.json --require-correct
python -m pytest -q tests/test_experience_screening.py
```

Choose a new report path for each run. The command refuses to overwrite a
report. It does not contact a model, database server, employer, or job board.

## Measured result

The [fixed fixture](../eval/experience_screening_v1.json) contains six
development and eight holdout cases. Groups were fixed in commit
`1f46194` while the ranking code was unchanged from `68c1474`.
Labels were authored by the implementation assistant and have no independent
human validation. Each timed result used 30 calls to `rank_job` per listing
on Windows with Python 3.13.15. See [baseline](evidence/experience-baseline.json)
and [after](evidence/experience-after.json).

| Holdout measure | Before | After |
|---|---:|---:|
| Hard-constraint violations among known-ineligible cases | 2/3 | 0/3 |
| False rejections among eligible cases | 1/5 | 0/5 |
| Exact effective floor including unknown | 5/8 | 8/8 |
| Exact-number extraction precision | 4/7 | 6/6 |
| Exact-number extraction recall | 4/6 | 6/6 |
| Ranking-call latency p50 / p95 | 68.5 / 86.2 µs | 62.1 / 81.9 µs |

The change preserves Greenhouse section breaks while retaining normalized
fingerprints. A regression test runs a cached Greenhouse payload through
normalization, SQLAlchemy persistence, the normal ranker and the actual
snapshot writer. It reopens a scratch SQLite database and replaces the same
snapshot twice. SQLite exercises this focused persistence path. PostgreSQL
migrations, pgvector, Temporal worker replay and live fetch are outside the run.

## Limits

Optional clauses, absent numbers and ambiguous alternatives can stay unknown.
Legacy flattened listings and unrecognized headings may lose context. The
fixture measures the effective numeric screening floor, with no per-skill
qualification decision or separate ranking relevance labels. Source freshness
and closed/unknown lifecycle decisions have distinct pending evaluation cases.
The latency numbers describe this micro-workload and are not a speed claim.
