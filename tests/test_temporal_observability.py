from prometheus_client import (
    generate_latest,
)

from jobintel.temporal_pipeline.observability import (
    normalize_step_name,
    record_activity_execution,
    record_pipeline_finalization,
)


def test_empty_step_name_is_normalized():
    assert (
        normalize_step_name(
            None
        )
        == "__none__"
    )


def test_real_step_name_is_preserved():
    assert (
        normalize_step_name(
            "Ranking"
        )
        == "Ranking"
    )


def test_activity_success_metric_is_exposed():
    record_activity_execution(
        activity_name=(
            "test_activity"
        ),
        step_name=(
            "Ranking"
        ),
        outcome=(
            "success"
        ),
        duration_seconds=(
            0.01
        ),
    )

    metrics = (
        generate_latest()
        .decode(
            "utf-8"
        )
    )

    assert (
        "jobintel_temporal_activity_executions_total"
        in metrics
    )

    assert (
        'activity_name="test_activity"'
        in metrics
    )

    assert (
        'step_name="Ranking"'
        in metrics
    )

    assert (
        'outcome="success"'
        in metrics
    )


def test_activity_duration_metric_is_exposed():
    record_activity_execution(
        activity_name=(
            "duration_test"
        ),
        step_name=(
            "JD enrichment"
        ),
        outcome=(
            "success"
        ),
        duration_seconds=(
            0.25
        ),
    )

    metrics = (
        generate_latest()
        .decode(
            "utf-8"
        )
    )

    assert (
        "jobintel_temporal_activity_duration_seconds"
        in metrics
    )


def test_pipeline_success_finalization_metric():
    record_pipeline_finalization(
        success=True
    )

    metrics = (
        generate_latest()
        .decode(
            "utf-8"
        )
    )

    assert (
        "jobintel_pipeline_finalizations_total"
        in metrics
    )

    assert (
        'success="true"'
        in metrics
    )


def test_pipeline_failure_finalization_metric():
    record_pipeline_finalization(
        success=False
    )

    metrics = (
        generate_latest()
        .decode(
            "utf-8"
        )
    )

    assert (
        'success="false"'
        in metrics
    )