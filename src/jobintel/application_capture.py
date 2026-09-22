from __future__ import annotations

import argparse
import json

from jobintel.application_ops.service import (
    history,
    set_status,
)
from jobintel.db.session import SessionLocal
from jobintel.profile.runtime import (
    DEFAULT_PROFILE_NAME,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Quickly capture a job application status and immutable history.")
    )

    parser.add_argument(
        "--job-id",
        required=True,
        type=int,
    )

    parser.add_argument(
        "--status",
        choices=[
            "new",
            "seen",
            "saved",
            "dismissed",
            "applied",
            "interviewing",
            "rejected",
            "offer",
        ],
    )

    parser.add_argument(
        "--notes",
        default=None,
    )

    parser.add_argument(
        "--history",
        action="store_true",
    )

    return parser.parse_args()


def record_to_dict(
    record,
) -> dict:
    payload = {}

    for column in record.__table__.columns:
        value = getattr(
            record,
            column.name,
        )

        if hasattr(
            value,
            "isoformat",
        ):
            value = value.isoformat()

        payload[column.name] = value

    return payload


def main() -> None:
    args = parse_args()

    if not args.status and not args.history:
        raise SystemExit("Provide --status and/or --history.")

    with SessionLocal() as session:
        if args.status:
            state = set_status(
                session=session,
                job_id=args.job_id,
                profile_name=(DEFAULT_PROFILE_NAME),
                status=args.status,
                notes=args.notes,
                source=("application_capture_cli"),
            )

            print(
                json.dumps(
                    {"updated_state": (record_to_dict(state))},
                    indent=2,
                    default=str,
                )
            )

        if args.history:
            records = history(
                session=session,
                job_id=args.job_id,
                profile_name=(DEFAULT_PROFILE_NAME),
            )

            print(
                json.dumps(
                    {"history": [record_to_dict(record) for record in records]},
                    indent=2,
                    default=str,
                )
            )


if __name__ == "__main__":
    main()
