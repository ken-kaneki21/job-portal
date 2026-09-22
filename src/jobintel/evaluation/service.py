from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from jobintel.db.models import (
    JobApplicationStateRecord,
    JobRankingRecord,
)
from jobintel.evaluation.metrics import (
    EvalItem,
    RankingMetrics,
    evaluate_ranking,
)
from jobintel.evaluation.variants import (
    DEFAULT_VARIANTS,
    ScoreComponents,
    ScoreVariant,
)
from jobintel.profile.models import CandidateProfile

POSITIVE_OUTCOMES = {
    "interviewing",
    "offer",
}

NEGATIVE_OUTCOMES = {
    "rejected",
}

COMPLETED_OUTCOMES = POSITIVE_OUTCOMES | NEGATIVE_OUTCOMES


@dataclass(frozen=True)
class EvaluationSample:
    job_id: int
    outcome: str
    positive: bool
    components: ScoreComponents


@dataclass(frozen=True)
class VariantEvaluation:
    variant: str
    metrics: RankingMetrics

    def to_dict(self) -> dict:
        return {
            "variant": self.variant,
            "metrics": (self.metrics.to_dict()),
        }


@dataclass(frozen=True)
class RegressionGate:
    passed: bool
    baseline_variant: str
    candidate_variant: str
    checks: dict[str, bool]
    deltas: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "baseline_variant": (self.baseline_variant),
            "candidate_variant": (self.candidate_variant),
            "checks": self.checks,
            "deltas": self.deltas,
        }


def latest_ranking_for_job(
    *,
    session,
    job_id: int,
    profile_name: str,
):
    return session.scalar(
        select(JobRankingRecord)
        .where(JobRankingRecord.job_id == job_id)
        .where(JobRankingRecord.profile_name == profile_name)
        .order_by(
            JobRankingRecord.ranked_at.desc(),
            JobRankingRecord.id.desc(),
        )
        .limit(1)
    )


def build_evaluation_samples(
    *,
    session,
    profile: CandidateProfile,
) -> list[EvaluationSample]:
    states = session.scalars(
        select(JobApplicationStateRecord)
        .where(JobApplicationStateRecord.profile_name == profile.name)
        .where(JobApplicationStateRecord.status.in_(tuple(COMPLETED_OUTCOMES)))
    ).all()

    samples: list[EvaluationSample] = []

    for state in states:
        ranking = latest_ranking_for_job(
            session=session,
            job_id=state.job_id,
            profile_name=profile.name,
        )

        if ranking is None:
            continue

        outcome = str(state.status)

        samples.append(
            EvaluationSample(
                job_id=state.job_id,
                outcome=outcome,
                positive=(outcome in POSITIVE_OUTCOMES),
                components=ScoreComponents(
                    stored_score=float(ranking.score or 0.0),
                    deterministic_score=float(ranking.deterministic_score or 0.0),
                    semantic_score=float(ranking.semantic_score or 0.0),
                    gap_score=float(ranking.gap_score or 0.0),
                ),
            )
        )

    return samples


def evaluate_variant(
    samples: list[EvaluationSample],
    *,
    variant: ScoreVariant,
    ks: tuple[int, ...],
) -> VariantEvaluation:
    items = [
        EvalItem(
            job_id=sample.job_id,
            score=variant.score(sample.components),
            positive=sample.positive,
            outcome=sample.outcome,
        )
        for sample in samples
    ]

    return VariantEvaluation(
        variant=variant.name,
        metrics=evaluate_ranking(
            items,
            ks=ks,
        ),
    )


def evaluate_variants(
    samples: list[EvaluationSample],
    *,
    variants: tuple[
        ScoreVariant,
        ...,
    ] = DEFAULT_VARIANTS,
    ks: tuple[int, ...] = (
        5,
        10,
        20,
    ),
) -> list[VariantEvaluation]:
    return [
        evaluate_variant(
            samples,
            variant=variant,
            ks=ks,
        )
        for variant in variants
    ]


def compare_variants(
    *,
    baseline: VariantEvaluation,
    candidate: VariantEvaluation,
    primary_k: int = 10,
    max_precision_drop: float = 0.05,
    max_pairwise_drop: float = 0.03,
) -> RegressionGate:
    baseline_precision = baseline.metrics.precision_at_k.get(
        primary_k,
        0.0,
    )
    candidate_precision = candidate.metrics.precision_at_k.get(
        primary_k,
        0.0,
    )

    precision_delta = candidate_precision - baseline_precision

    pairwise_delta = (
        candidate.metrics.pairwise_accuracy - baseline.metrics.pairwise_accuracy
    )

    checks = {
        f"precision_at_{primary_k}": (precision_delta >= -max_precision_drop),
        "pairwise_accuracy": (pairwise_delta >= -max_pairwise_drop),
    }

    return RegressionGate(
        passed=all(checks.values()),
        baseline_variant=(baseline.variant),
        candidate_variant=(candidate.variant),
        checks=checks,
        deltas={
            f"precision_at_{primary_k}": round(
                precision_delta,
                4,
            ),
            "pairwise_accuracy": round(
                pairwise_delta,
                4,
            ),
        },
    )


def run_offline_evaluation(
    *,
    session,
    profile: CandidateProfile,
    ks: tuple[int, ...] = (
        5,
        10,
        20,
    ),
) -> dict:
    samples = build_evaluation_samples(
        session=session,
        profile=profile,
    )

    evaluations = evaluate_variants(
        samples,
        ks=ks,
    )

    by_name = {item.variant: item for item in evaluations}

    baseline = by_name["stored_live_score"]

    gates = [
        compare_variants(
            baseline=baseline,
            candidate=item,
            primary_k=10,
        )
        for item in evaluations
        if item.variant != baseline.variant
    ]

    return {
        "profile_name": profile.name,
        "sample_count": len(samples),
        "positive_outcomes": sum(1 for sample in samples if sample.positive),
        "negative_outcomes": sum(1 for sample in samples if not sample.positive),
        "variants": [item.to_dict() for item in evaluations],
        "regression_gates": [gate.to_dict() for gate in gates],
        "warning": (
            None
            if len(samples) >= 10
            else ("Small historical outcome set; treat metrics as directional only.")
        ),
    }
