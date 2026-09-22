from __future__ import annotations

import argparse
import json

from jobintel.profile.llm_enrichment import (
    apply_profile_enrichment,
    request_profile_enrichment,
)
from jobintel.resume.service import (
    load_universal_profile,
    persist_profile,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Optionally enrich the DB-backed universal candidate profile using an LLM."
        )
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist the enriched profile. Default is preview-only.",
    )
    parser.add_argument(
        "--use-suggested-summary",
        action="store_true",
        help="Allow the LLM suggestion to replace the deterministic summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = load_universal_profile()

    if profile is None:
        raise RuntimeError("No universal candidate profile is configured.")

    enrichment = request_profile_enrichment(profile)

    enriched = apply_profile_enrichment(
        profile,
        enrichment,
        use_suggested_summary=args.use_suggested_summary,
    )

    print(
        json.dumps(
            enrichment.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        )
    )

    if args.persist:
        persist_profile(enriched)
        print()
        print("Enriched profile persisted.")
    else:
        print()
        print("Preview only. Use --persist to save.")


if __name__ == "__main__":
    main()
