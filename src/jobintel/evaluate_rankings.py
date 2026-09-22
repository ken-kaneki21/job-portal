from __future__ import annotations

import argparse
import json

from jobintel.db.session import SessionLocal
from jobintel.evaluation.service import run_offline_evaluation
from jobintel.profile.runtime import load_active_candidate_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate ranking variants against historical "
            "completed application outcomes without changing "
            "live rankings."
        )
    )

    parser.add_argument(
        "--k",
        nargs="+",
        type=int,
        default=[
            5,
            10,
            20,
        ],
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    profile = load_active_candidate_profile()

    with SessionLocal() as session:
        report = run_offline_evaluation(
            session=session,
            profile=profile,
            ks=tuple(args.k),
        )

    print(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
