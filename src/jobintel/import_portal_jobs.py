from __future__ import annotations

import argparse
import json
from pathlib import Path

from jobintel.db.broad_repository import persist_broad_jobs
from jobintel.db.session import SessionLocal
from jobintel.search_sources.portal_import import (
    SUPPORTED_PORTALS,
    inspect_portal_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import user-provided LinkedIn, Naukri, Foundit, or Indeed job exports."
        )
    )
    parser.add_argument("--portal", required=True, choices=sorted(SUPPORTED_PORTALS))
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and summarize without writing to the database.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any import row is invalid.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = inspect_portal_file(portal=args.portal, path=args.file)
    summary = report.summary_dict()

    if args.strict and report.invalid_rows:
        raise SystemExit(
            f"Strict import rejected {report.invalid_rows} invalid row(s)."
        )

    if args.dry_run:
        summary["persisted"] = False
    else:
        with SessionLocal() as session:
            result = persist_broad_jobs(
                session=session,
                fetched_jobs=list(report.jobs),
            )
            session.commit()

        summary.update(
            {
                "persisted": True,
                "new_canonical_jobs": result.new,
                "matched_existing": result.matched_existing,
                "already_known": result.existing_source,
                "raw_payloads_saved": result.raw_saved,
            }
        )

    if args.json:
        print(json.dumps(summary, indent=2, default=str))
        return

    print(f"Portal:             {report.portal}")
    print(f"Input rows:         {report.total_rows}")
    print(f"Valid rows:         {report.valid_rows}")
    print(f"Invalid rows:       {report.invalid_rows}")
    print(f"In-file duplicates: {report.duplicate_rows}")

    for issue in report.issues[:10]:
        print(f"  row {issue.row_number}: {issue.message}")

    if args.dry_run:
        print("Dry run: no database writes performed.")
        return

    print(f"New canonical jobs: {summary['new_canonical_jobs']}")
    print(f"Matched existing:   {summary['matched_existing']}")
    print(f"Already known:      {summary['already_known']}")
    print(f"Raw payloads saved: {summary['raw_payloads_saved']}")


if __name__ == "__main__":
    main()
