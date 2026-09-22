from __future__ import annotations

import argparse
from pathlib import Path

from jobintel.db.broad_repository import persist_broad_jobs
from jobintel.db.session import SessionLocal
from jobintel.search_sources.portal_import import (
    SUPPORTED_PORTALS,
    load_portal_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import user-provided LinkedIn, Naukri, Foundit, or Indeed job exports."
        )
    )
    parser.add_argument(
        "--portal",
        required=True,
        choices=sorted(SUPPORTED_PORTALS),
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    jobs = load_portal_file(
        portal=args.portal,
        path=args.file,
    )

    with SessionLocal() as session:
        result = persist_broad_jobs(
            session=session,
            fetched_jobs=jobs,
        )
        session.commit()

    print(f"Portal:             {args.portal}")
    print(f"Valid import rows:  {len(jobs)}")
    print(f"New canonical jobs: {result.new}")
    print(f"Matched existing:   {result.matched_existing}")
    print(f"Already known:      {result.existing_source}")
    print(f"Raw payloads saved: {result.raw_saved}")


if __name__ == "__main__":
    main()
