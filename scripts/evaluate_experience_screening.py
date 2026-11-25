"""Run the frozen experience-screening cases through the actual ranking entry point."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from jobintel.db.models import JobRecord
from jobintel.profile.models import CandidateProfile
from jobintel.ranking.scoring import rank_job


def evaluate(fixture):
    profile = CandidateProfile(
        name="synthetic-screening-profile",
        target_titles=["AI Engineer", "Data Engineer", "Python Backend Engineer"],
        adjacent_titles=[],
        exclude_titles=[],
        preferred_locations=["Bengaluru"],
        allowed_countries=["India"],
        blocked_location_terms=["United States"],
        core_skills=["Python", "SQL"],
        secondary_skills=[],
        max_preferred_experience_years=3,
        hard_max_experience_years=fixture["candidate_hard_max_years"],
    )
    rows = []
    for case in fixture["cases"]:
        job = JobRecord(
            title=case["title"],
            location=case["location"],
            description=case["description"],
            apply_url=case["source_url"]
            or "https://example.invalid/jobs/" + case["id"],
            first_seen_at=datetime(2026, 11, 24, tzinfo=UTC),
        )
        samples = []
        for _ in range(30):
            start = perf_counter_ns()
            result = rank_job(job, profile)
            samples.append((perf_counter_ns() - start) / 1000)
        rows.append(
            {
                "id": case["id"],
                "split": case["split"],
                "expected_years": case["expected_years"],
                "actual_years": result.detected_experience,
                "expected_eligible": case["eligible"],
                "actual_eligible": result.eligible,
                "rejections": result.rejection_reasons,
                "latency_us": samples,
            }
        )
    return rows


def summarize(rows):
    truth = sum(row["expected_years"] is not None for row in rows)
    predicted = sum(row["actual_years"] is not None for row in rows)
    exact = sum(
        row["expected_years"] is not None
        and row["expected_years"] == row["actual_years"]
        for row in rows
    )
    negative = sum(not row["expected_eligible"] for row in rows)
    violations = sum(
        not row["expected_eligible"] and row["actual_eligible"] for row in rows
    )
    samples = sorted(sample for row in rows for sample in row["latency_us"])
    return {
        "cases": len(rows),
        "exact_years_with_unknown": sum(
            row["expected_years"] == row["actual_years"] for row in rows
        ),
        "extraction_precision": exact / predicted if predicted else None,
        "extraction_recall": exact / truth if truth else None,
        "ineligible_cases": negative,
        "hard_constraint_violations": violations,
        "hard_constraint_violation_rate": violations / negative if negative else None,
        "false_rejections": sum(
            row["expected_eligible"] and not row["actual_eligible"] for row in rows
        ),
        "latency_samples": len(samples),
        "p50_us": median(samples),
        "p95_us": samples[(95 * len(samples) + 99) // 100 - 1],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-correct", action="store_true")
    parser.add_argument(
        "--fixture", type=Path, default=Path("eval/experience_screening_v1.json")
    )
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    rows = evaluate(fixture)
    report = {
        "dataset": fixture["version"],
        "label_provenance": fixture["label_provenance"],
        "metrics": {
            split: summarize([row for row in rows if row["split"] == split])
            for split in ("dev", "holdout")
        },
        "cases": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps(report["metrics"], indent=2))
    return int(
        args.require_correct
        and any(
            row["expected_years"] != row["actual_years"]
            or row["expected_eligible"] != row["actual_eligible"]
            for row in rows
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
