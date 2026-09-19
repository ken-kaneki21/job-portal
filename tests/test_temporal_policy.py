from jobintel.pipeline import STEPS
from jobintel.temporal_pipeline.workflow import (
    BEST_EFFORT_STEPS,
    CRITICAL_STEPS,
    is_best_effort_step,
)


def test_critical_and_best_effort_do_not_overlap():
    assert (CRITICAL_STEPS & BEST_EFFORT_STEPS) == set()


def test_all_pipeline_steps_have_policy():
    pipeline_labels = {label for label, module in STEPS}

    configured = CRITICAL_STEPS | BEST_EFFORT_STEPS

    assert pipeline_labels == configured


def test_direct_ats_is_critical():
    assert "Direct ATS ingestion" in CRITICAL_STEPS

    assert not is_best_effort_step("Direct ATS ingestion")


def test_ranking_is_critical():
    assert "Ranking" in CRITICAL_STEPS

    assert not is_best_effort_step("Ranking")


def test_data_quality_is_critical():
    assert "Data quality checks" in CRITICAL_STEPS


def test_broad_search_is_best_effort():
    assert "Broad search" in BEST_EFFORT_STEPS

    assert is_best_effort_step("Broad search")


def test_notifications_are_best_effort():
    notification_steps = {
        "Queue notifications",
        "Retry failed notifications",
        "Deliver notifications",
    }

    assert notification_steps.issubset(BEST_EFFORT_STEPS)


def test_company_discovery_is_best_effort():
    assert is_best_effort_step("Queue company discovery candidates")

    assert is_best_effort_step("Resolve company ATS")


def test_core_intelligence_steps_are_critical():
    expected = {
        "JD enrichment",
        "Refresh job embeddings",
        "Candidate JD gap analysis",
        "Ranking",
    }

    assert expected.issubset(CRITICAL_STEPS)
