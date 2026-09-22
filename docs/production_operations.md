# Production Operations

This milestone hardens the practical job-search workflow without enabling blind final submission.

## Portal imports

Supported user-assisted sources:

- LinkedIn
- Naukri
- Foundit
- Indeed

CSV, TSV, and JSON are accepted.

Validate without writing:

```bat
python -m jobintel.import_portal_jobs --portal linkedin --file jobs.csv --dry-run
```

Strict validation:

```bat
python -m jobintel.import_portal_jobs --portal naukri --file jobs.csv --dry-run --strict
```

Machine-readable summary:

```bat
python -m jobintel.import_portal_jobs --portal indeed --file jobs.json --dry-run --json
```

Persist:

```bat
python -m jobintel.import_portal_jobs --portal foundit --file jobs.csv
```

Imports include row-level provenance and in-file duplicate removal before the existing canonical persistence layer runs.

## Applications UI

The Applications page is backed by the real API and shows saved, applied, interviewing, rejected, and offer states.

Selecting a job opens a workspace with status controls, notes, immutable history, readiness checks, generated application assets, reusable answers, and a Workday assist command.

## Workday assist

```bat
python -m jobintel.workday_autofill --job-id 123
```

Optional resume:

```bat
python -m jobintel.workday_autofill --job-id 123 --resume path\to\resume.pdf
```

Optional diagnostic screenshot:

```bat
python -m jobintel.workday_autofill --job-id 123 --screenshot output\workday-review.png
```

The browser helper fills supported visible fields, reports remaining required fields, identifies whether final submit is visible, and never clicks the final Submit button.

## Safety boundary

This project does not scrape portal credentials and does not blindly submit job applications. The user remains responsible for reviewing application content and clicking final submission.
