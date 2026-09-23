from jobintel.evaluation.metrics import RankingMetrics
from jobintel.evaluation.service import (
    VariantEvaluation,
    compare_variants,
)
from jobintel.evaluation.variants import (
    ScoreComponents,
    ScoreVariant,
)


def test_score_variant_is_bounded():
    variant = ScoreVariant(
        name="candidate",
        deterministic_weight=1.0,
        semantic_weight=1.0,
        gap_weight=1.0,
    )

    score = variant.score(
        ScoreComponents(
            stored_score=50.0,
            deterministic_score=90.0,
            semantic_score=10.0,
            gap_score=90.0,
        )
    )

    assert score == 100.0


def make_metrics(
    precision: float,
    pairwise: float,
) -> RankingMetrics:
    return RankingMetrics(
        sample_count=20,
        positive_count=5,
        base_positive_rate=0.25,
        precision_at_k={
            10: precision,
        },
        recall_at_k={
            10: 1.0,
        },
        lift_at_k={
            10: precision / 0.25,
        },
        pairwise_accuracy=pairwise,
    )


def test_regression_gate_allows_small_change():
    baseline = VariantEvaluation(
        variant="baseline",
        metrics=make_metrics(
            0.50,
            0.70,
        ),
    )

    candidate = VariantEvaluation(
        variant="candidate",
        metrics=make_metrics(
            0.47,
            0.68,
        ),
    )

    gate = compare_variants(
        baseline=baseline,
        candidate=candidate,
        primary_k=10,
    )

    assert gate.passed is True
    assert gate.evaluable is True
    assert gate.reason is None


def test_regression_gate_blocks_large_drop():
    baseline = VariantEvaluation(
        variant="baseline",
        metrics=make_metrics(
            0.50,
            0.70,
        ),
    )

    candidate = VariantEvaluation(
        variant="candidate",
        metrics=make_metrics(
            0.40,
            0.60,
        ),
    )

    gate = compare_variants(
        baseline=baseline,
        candidate=candidate,
        primary_k=10,
    )

    assert gate.passed is False
    assert gate.evaluable is True


def test_regression_gate_is_not_evaluable_without_samples():
    empty = RankingMetrics(
        sample_count=0,
        positive_count=0,
        base_positive_rate=0.0,
        precision_at_k={},
        recall_at_k={},
        lift_at_k={},
        pairwise_accuracy=0.0,
    )

    baseline = VariantEvaluation(
        variant="baseline",
        metrics=empty,
    )

    candidate = VariantEvaluation(
        variant="candidate",
        metrics=empty,
    )

    gate = compare_variants(
        baseline=baseline,
        candidate=candidate,
        primary_k=10,
    )

    assert gate.passed is None
    assert gate.evaluable is False
    assert gate.reason == "No completed application outcomes are available."
    assert gate.checks == {}
    assert gate.deltas == {}


def test_regression_gate_uses_effective_k_for_small_samples():
    baseline_metrics = RankingMetrics(
        sample_count=4,
        positive_count=2,
        base_positive_rate=0.5,
        precision_at_k={
            4: 0.50,
        },
        recall_at_k={
            4: 1.0,
        },
        lift_at_k={
            4: 1.0,
        },
        pairwise_accuracy=0.75,
    )

    candidate_metrics = RankingMetrics(
        sample_count=4,
        positive_count=2,
        base_positive_rate=0.5,
        precision_at_k={
            4: 0.50,
        },
        recall_at_k={
            4: 1.0,
        },
        lift_at_k={
            4: 1.0,
        },
        pairwise_accuracy=0.74,
    )

    gate = compare_variants(
        baseline=VariantEvaluation(
            variant="baseline",
            metrics=baseline_metrics,
        ),
        candidate=VariantEvaluation(
            variant="candidate",
            metrics=candidate_metrics,
        ),
        primary_k=10,
    )

    assert gate.evaluable is True
    assert gate.passed is True
    assert "precision_at_4" in gate.checks
    assert "precision_at_10" not in gate.checks
