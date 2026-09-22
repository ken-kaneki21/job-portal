from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreComponents:
    stored_score: float
    deterministic_score: float
    semantic_score: float
    gap_score: float


@dataclass(frozen=True)
class ScoreVariant:
    name: str
    stored_score_weight: float = 0.0
    deterministic_weight: float = 0.0
    semantic_weight: float = 0.0
    gap_weight: float = 0.0

    def score(
        self,
        components: ScoreComponents,
    ) -> float:
        value = (
            (components.stored_score * self.stored_score_weight)
            + (components.deterministic_score * self.deterministic_weight)
            + (components.semantic_score * self.semantic_weight)
            + (components.gap_score * self.gap_weight)
        )

        return round(
            max(
                0.0,
                min(
                    100.0,
                    value,
                ),
            ),
            4,
        )


DEFAULT_VARIANTS = (
    ScoreVariant(
        name="stored_live_score",
        stored_score_weight=1.0,
    ),
    ScoreVariant(
        name="stable_core_75_10_15",
        deterministic_weight=0.75,
        semantic_weight=1.0,
        gap_weight=0.15,
    ),
    ScoreVariant(
        name="deterministic_only",
        deterministic_weight=1.0,
    ),
    ScoreVariant(
        name="gap_heavier_70_10_20",
        deterministic_weight=0.70,
        semantic_weight=1.0,
        gap_weight=0.20,
    ),
)
