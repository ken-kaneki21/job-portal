from jobintel.temporal_pipeline.config import (
    TASK_QUEUE,
    TEMPORAL_ADDRESS,
    TEMPORAL_NAMESPACE,
)


def test_temporal_address_configured():
    assert TEMPORAL_ADDRESS
    assert ":" in TEMPORAL_ADDRESS


def test_temporal_namespace_configured():
    assert (
        TEMPORAL_NAMESPACE
        == "default"
    )


def test_temporal_task_queue_configured():
    assert (
        TASK_QUEUE
        == "job-intelligence-pipeline"
    )