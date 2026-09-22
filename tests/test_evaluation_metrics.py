from jobintel.evaluation.metrics import (
    EvalItem,
    evaluate_ranking,
)


def test_precision_recall_lift_and_pairwise():
    items = [
        EvalItem(
            job_id=1,
            score=95.0,
            positive=True,
            outcome="offer",
        ),
        EvalItem(
            job_id=2,
            score=90.0,
            positive=True,
            outcome="interviewing",
        ),
        EvalItem(
            job_id=3,
            score=80.0,
            positive=False,
            outcome="rejected",
        ),
        EvalItem(
            job_id=4,
            score=70.0,
            positive=False,
            outcome="rejected",
        ),
    ]

    metrics = evaluate_ranking(
        items,
        ks=(2, 4),
    )

    assert metrics.sample_count == 4
    assert metrics.positive_count == 2
    assert metrics.precision_at_k[2] == 1.0
    assert metrics.recall_at_k[2] == 1.0
    assert metrics.lift_at_k[2] == 2.0
    assert metrics.pairwise_accuracy == 1.0
