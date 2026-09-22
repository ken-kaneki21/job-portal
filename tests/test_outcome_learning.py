from jobintel.outcome_learning.features import OutcomeFeatures
from jobintel.outcome_learning.service import (
    FeatureStat,
    OutcomeModel,
    score_outcome_adjustment,
)


def make_features():
    return OutcomeFeatures(
        source="linkedin",
        title_family="data_engineering",
        location_family="bengaluru",
        experience_band="0-2",
        skill_signature="python+sql",
        deterministic_band="70-80",
        semantic_band="6-8",
        gap_band="80-90",
    )


def test_learning_is_inactive_with_too_few_outcomes():
    model = OutcomeModel(
        sample_count=4,
        global_mean=0.0,
        feature_stats={
            ("source", "linkedin"): FeatureStat(
                feature_type="source",
                feature_value="linkedin",
                count=4,
                mean_outcome=1.0,
                global_mean=0.0,
                adjustment=2.0,
            )
        },
    )

    result = score_outcome_adjustment(
        model=model,
        features=make_features(),
    )

    assert result.score == 0.0
    assert result.reasons == ()


def test_adjustment_is_bounded_and_explained():
    model = OutcomeModel(
        sample_count=12,
        global_mean=0.0,
        feature_stats={
            ("source", "linkedin"): FeatureStat(
                feature_type="source",
                feature_value="linkedin",
                count=6,
                mean_outcome=1.2,
                global_mean=0.0,
                adjustment=2.5,
            ),
            ("title_family", "data_engineering"): FeatureStat(
                feature_type="title_family",
                feature_value="data_engineering",
                count=8,
                mean_outcome=1.0,
                global_mean=0.0,
                adjustment=2.0,
            ),
        },
    )

    result = score_outcome_adjustment(
        model=model,
        features=make_features(),
    )

    assert 0.0 < result.score <= 5.0
    assert result.sample_count == 12
    assert any("source=linkedin" in reason for reason in result.reasons)
