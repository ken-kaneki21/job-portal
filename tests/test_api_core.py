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
    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["info"]["title"]
        == "Job Intelligence API"
    )


def test_expected_routes_exist():
    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    schema = response.json()

    paths = set(
        schema.get(
            "paths",
            {}
        ).keys()
    )

    expected = {
        "/",
        "/health",
        "/jobs",
        "/jobs/{job_id}",
        "/rankings",
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

    missing = (
        expected
        - paths
    )

    assert not missing, (
        "Missing expected API routes: "
        f"{sorted(missing)}\n"
        "Actual OpenAPI routes: "
        f"{sorted(paths)}"
    )


def test_pipeline_run_uses_temporal(
    monkeypatch,
):
    async def fake_start():
        return {
            "message": (
                "Temporal pipeline workflow started"
            ),
            "workflow_id": (
                "test-workflow-123"
            ),
            "temporal_managed": True,
            "task_queue": (
                "job-intelligence-pipeline"
            ),
        }

    monkeypatch.setattr(
        api_module,
        "start_temporal_pipeline",
        fake_start,
    )

    response = client.post(
        "/pipeline/run"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["workflow_id"]
        == "test-workflow-123"
    )

    assert (
        payload["temporal_managed"]
        is True
    )

    assert (
        payload["task_queue"]
        == "job-intelligence-pipeline"
    )