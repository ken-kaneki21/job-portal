from fastapi.testclient import TestClient

import jobintel.api as api_module
from jobintel.api import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()

    assert payload["service"] == "job-intelligence"
    assert payload["version"] == "0.3.0"
    assert payload["docs"] == "/docs"
    assert payload["health"] == "/health"


def test_openapi_is_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    payload = response.json()

    assert payload["info"]["title"] == "Job Intelligence API"


def test_expected_routes_exist():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    paths = set(
        schema.get(
            "paths",
            {},
        ).keys()
    )

    expected = {
        "/",
        "/health",
        "/jobs",
        "/jobs/{job_id}",
        "/rankings",
        "/rankings/stats",
        "/shortlist",
        "/saved-jobs",
        "/applications",
        "/application-state-summary",
        "/pipeline-runs",
        "/pipeline-runs/{run_id}",
        "/pipeline/run",
        "/stats",
        "/jobs/{job_id}/state",
        "/jobs/{job_id}/history",
        "/jobs/{job_id}/application-assets",
        "/jobs/{job_id}/regenerate-assets",
        "/temporal/workflows/{workflow_id}",
        "/temporal/workflows/{workflow_id}/result",
    }

    missing = expected - paths

    assert not missing, (
        "Missing expected API routes: "
        f"{sorted(missing)}\n"
        "Actual OpenAPI routes: "
        f"{sorted(paths)}"
    )


def test_ranking_stats(
    monkeypatch,
):
    class FakeResult:
        def all(self):
            return [
                (
                    "high_confidence",
                    1,
                ),
                (
                    "discovery",
                    466,
                ),
                (
                    "stretch",
                    100,
                ),
            ]

    class FakeSession:
        def scalar(
            self,
            statement,
        ):
            del statement

            return 567

        def execute(
            self,
            statement,
        ):
            del statement

            return FakeResult()

    monkeypatch.setattr(
        api_module,
        "latest_pipeline_ranking_run_id",
        lambda session: 28,
    )

    payload = api_module.get_ranking_stats(
        profile_name="universal",
        pipeline_run_id=None,
        session=FakeSession(),
    )

    assert payload["profile_name"] == "universal"

    assert payload["pipeline_run_id"] == 28

    assert payload["total"] == 567

    assert payload["buckets"] == {
        "high_confidence": 1,
        "discovery": 466,
        "stretch": 100,
    }


def test_ranking_stats_without_run(
    monkeypatch,
):
    class FakeSession:
        pass

    monkeypatch.setattr(
        api_module,
        "latest_pipeline_ranking_run_id",
        lambda session: None,
    )

    payload = api_module.get_ranking_stats(
        profile_name="universal",
        pipeline_run_id=None,
        session=FakeSession(),
    )

    assert payload == {
        "profile_name": "universal",
        "pipeline_run_id": None,
        "total": 0,
        "buckets": {
            "high_confidence": 0,
            "discovery": 0,
            "stretch": 0,
        },
    }


def test_pipeline_run_uses_temporal(
    monkeypatch,
):
    async def fake_start():
        return {
            "message": ("Temporal pipeline workflow started"),
            "workflow_id": ("test-workflow-123"),
            "temporal_managed": True,
            "task_queue": ("job-intelligence-pipeline"),
        }

    monkeypatch.setattr(
        api_module,
        "start_temporal_pipeline",
        fake_start,
    )

    response = client.post("/pipeline/run")

    assert response.status_code == 200

    payload = response.json()

    assert payload["workflow_id"] == "test-workflow-123"

    assert payload["temporal_managed"] is True

    assert payload["task_queue"] == "job-intelligence-pipeline"
