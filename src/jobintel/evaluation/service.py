from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select

from jobintel.db.application_event_model import (
    JobApplicationEventRecord,
)
from jobintel.db.models import (
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
from jobintel.outcome_learning.history import (
    derive_historical_outcome,
)
from jobintel.profile.models import CandidateProfile


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
            "metrics": self.metrics.to_dict(),
        }


@dataclass(frozen=True)
class RegressionGate:
    passed: bool | None
    evaluable: bool
    reason: str | None
    baseline_variant: str
    candidate_variant: str
    checks: dict[str, bool]
    deltas: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "evaluable": self.evaluable,
            "reason": self.reason,
            "baseline_variant": self.baseline_variant,
            "candidate_variant": self.candidate_variant,
            "checks": self.checks,
            "deltas": self.deltas,
        }


def latest_ranking_at_or_before(
    *,
    session,
    job_id: int,
    profile_name: str,
    at,
):
    return session.scalar(
        select(JobRankingRecord)
        .where(JobRankingRecord.job_id == job_id)
        .where(JobRankingRecord.profile_name == profile_name)
        .where(JobRankingRecord.ranked_at <= at)
        .order_by(
            JobRankingRecord.ranked_at.desc(),
            JobRankingRecord.id.desc(),
        )
        .limit(1)
    )


def application_histories(
    *,
    session,
    profile_name: str,
) -> dict[int, list[JobApplicationEventRecord]]:
    events = session.scalars(
        select(JobApplicationEventRecord)
        .where(JobApplicationEventRecord.profile_name == profile_name)
        .order_by(
            JobApplicationEventRecord.job_id.asc(),
            JobApplicationEventRecord.created_at.asc(),
            JobApplicationEventRecord.id.asc(),
        )
    ).all()

    histories: dict[int, list[JobApplicationEventRecord]] = defaultdict(list)

    for event in events:
        histories[event.job_id].append(event)

    return histories


def build_evaluation_samples(
    *,
    session,
    profile: CandidateProfile,
) -> list[EvaluationSample]:
    histories = application_histories(
        session=session,
        profile_name=profile.name,
    )

    samples: list[EvaluationSample] = []

    for job_id, events in histories.items():
        historical_outcome = derive_historical_outcome(events)

        if historical_outcome is None:
            continue

        ranking = latest_ranking_at_or_before(
            session=session,
            job_id=job_id,
            profile_name=profile.name,
            at=historical_outcome.applied_at,
        )

        if ranking is None:
            continue

        samples.append(
            EvaluationSample(
                job_id=job_id,
                outcome=historical_outcome.outcome,
                positive=historical_outcome.positive,
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
    variants: tuple[ScoreVariant, ...] = DEFAULT_VARIANTS,
    ks: tuple[int, ...] = (5, 10, 20),
) -> list[VariantEvaluation]:
    return [
        evaluate_variant(
            samples,
            variant=variant,
            ks=ks,
        )
        for variant in variants
    ]


def effective_metric_k(
    metrics: RankingMetrics,
    requested_k: int,
) -> int | None:
    available = sorted(metrics.precision_at_k)

    if not available:
        return None

    eligible = [value for value in available if value <= requested_k]

    if eligible:
        return max(eligible)

    return min(available)


def compare_variants(
    *,
    baseline: VariantEvaluation,
    candidate: VariantEvaluation,
    primary_k: int = 10,
    max_precision_drop: float = 0.05,
    max_pairwise_drop: float = 0.03,
) -> RegressionGate:
    if baseline.metrics.sample_count == 0:
        return RegressionGate(
            passed=None,
            evaluable=False,
            reason="No completed application outcomes are available.",
            baseline_variant=baseline.variant,
            candidate_variant=candidate.variant,
            checks={},
            deltas={},
        )

    baseline_k = effective_metric_k(
        baseline.metrics,
        primary_k,
    )
    candidate_k = effective_metric_k(
        candidate.metrics,
        primary_k,
    )

    if baseline_k is None or candidate_k is None:
        return RegressionGate(
            passed=None,
            evaluable=False,
            reason="Precision metrics are not available for comparison.",
            baseline_variant=baseline.variant,
            candidate_variant=candidate.variant,
            checks={},
            deltas={},
        )

    comparison_k = min(
        baseline_k,
        candidate_k,
    )

    baseline_precision = baseline.metrics.precision_at_k[comparison_k]
    candidate_precision = candidate.metrics.precision_at_k[comparison_k]

    precision_delta = candidate_precision - baseline_precision

    pairwise_delta = (
        candidate.metrics.pairwise_accuracy - baseline.metrics.pairwise_accuracy
    )

    checks = {
        f"precision_at_{comparison_k}": (precision_delta >= -max_precision_drop),
        "pairwise_accuracy": (pairwise_delta >= -max_pairwise_drop),
    }

    return RegressionGate(
        passed=all(checks.values()),
        evaluable=True,
        reason=None,
        baseline_variant=baseline.variant,
        candidate_variant=candidate.variant,
        checks=checks,
        deltas={
            f"precision_at_{comparison_k}": round(
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
    ks: tuple[int, ...] = (5, 10, 20),
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

    sample_count = len(samples)

    if sample_count == 0:
        warning = (
            "No historically valid completed application outcomes are available; "
            "ranking variants cannot be evaluated yet."
        )
    elif sample_count < 10:
        warning = (
            "Small historically valid outcome set; "
            "treat metrics as directional only."
        )
    else:
        warning = None

    return {
        "profile_name": profile.name,
        "sample_count": sample_count,
        "positive_outcomes": sum(1 for sample in samples if sample.positive),
        "negative_outcomes": sum(1 for sample in samples if not sample.positive),
        "variants": [item.to_dict() for item in evaluations],
        "regression_gates": [gate.to_dict() for gate in gates],
        "warning": warning,
    }
