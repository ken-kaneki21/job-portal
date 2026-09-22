from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalItem:
    job_id: int
    score: float
    positive: bool
    outcome: str


@dataclass(frozen=True)
class RankingMetrics:
    sample_count: int
    positive_count: int
    base_positive_rate: float
    precision_at_k: dict[int, float]
    recall_at_k: dict[int, float]
    lift_at_k: dict[int, float]
    pairwise_accuracy: float

    def to_dict(self) -> dict:
        return {
            "sample_count": self.sample_count,
            "positive_count": self.positive_count,
            "base_positive_rate": self.base_positive_rate,
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "lift_at_k": self.lift_at_k,
            "pairwise_accuracy": self.pairwise_accuracy,
        }


def normalize_ks(
    ks: tuple[int, ...],
    *,
    sample_count: int,
) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                max(
                    1,
                    min(
                        int(k),
                        sample_count,
                    ),
                )
                for k in ks
                if int(k) > 0
            }
        )
    )


def pairwise_accuracy(
    items: list[EvalItem],
) -> float:
    positives = [item for item in items if item.positive]
    negatives = [item for item in items if not item.positive]

    total = 0
    correct = 0.0

    for positive in positives:
        for negative in negatives:
            total += 1

            if positive.score > negative.score:
                correct += 1.0
            elif positive.score == negative.score:
                correct += 0.5

    if total == 0:
        return 0.0

    return round(
        correct / total,
        4,
    )


def evaluate_ranking(
    items: list[EvalItem],
    *,
    ks: tuple[int, ...] = (
        5,
        10,
        20,
    ),
) -> RankingMetrics:
    if not items:
        return RankingMetrics(
            sample_count=0,
            positive_count=0,
            base_positive_rate=0.0,
            precision_at_k={},
            recall_at_k={},
            lift_at_k={},
            pairwise_accuracy=0.0,
        )

    ranked = sorted(
        items,
        key=lambda item: (
            item.score,
            -item.job_id,
        ),
        reverse=True,
    )

    positive_count = sum(1 for item in ranked if item.positive)

    base_rate = positive_count / len(ranked)

    precision: dict[int, float] = {}
    recall: dict[int, float] = {}
    lift: dict[int, float] = {}

    for k in normalize_ks(
        ks,
        sample_count=len(ranked),
    ):
        top = ranked[:k]

        top_positive = sum(1 for item in top if item.positive)

        precision_value = top_positive / len(top)

        recall_value = top_positive / positive_count if positive_count else 0.0

        lift_value = precision_value / base_rate if base_rate else 0.0

        precision[k] = round(
            precision_value,
            4,
        )
        recall[k] = round(
            recall_value,
            4,
        )
        lift[k] = round(
            lift_value,
            4,
        )

    return RankingMetrics(
        sample_count=len(ranked),
        positive_count=positive_count,
        base_positive_rate=round(
            base_rate,
            4,
        ),
        precision_at_k=precision,
        recall_at_k=recall,
        lift_at_k=lift,
        pairwise_accuracy=pairwise_accuracy(ranked),
    )
