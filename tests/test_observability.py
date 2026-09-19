from fastapi.testclient import (
    TestClient,
)

from jobintel.api import app


client = TestClient(
    app
)


def test_request_id_is_generated():
    response = client.get(
        "/"
    )

    assert (
        response.status_code
        == 200
    )

    request_id = (
        response.headers.get(
            "X-Request-ID"
        )
    )

    assert request_id
    assert len(
        request_id
    ) > 10


def test_existing_request_id_is_preserved():
    request_id = (
        "jobintel-test-request-123"
    )

    response = client.get(
        "/",
        headers={
            "X-Request-ID": (
                request_id
            ),
        },
    )

    assert (
        response.status_code
        == 200
    )

    assert (
        response.headers[
            "X-Request-ID"
        ]
        == request_id
    )


def test_metrics_endpoint_exists():
    response = client.get(
        "/metrics"
    )

    assert (
        response.status_code
        == 200
    )

    assert (
        "text/plain"
        in response.headers[
            "content-type"
        ]
    )


def test_api_request_counter_is_exposed():
    client.get(
        "/"
    )

    response = client.get(
        "/metrics"
    )

    assert (
        response.status_code
        == 200
    )

    metrics = (
        response.text
    )

    assert (
        "jobintel_api_requests_total"
        in metrics
    )


def test_api_duration_metric_is_exposed():
    client.get(
        "/"
    )

    response = client.get(
        "/metrics"
    )

    metrics = (
        response.text
    )

    assert (
        "jobintel_api_request_duration_seconds"
        in metrics
    )


def test_route_template_is_used_for_metrics():
    response = client.get(
        "/jobs/999999999"
    )

    assert response.status_code in {
        404,
        200,
    }

    metrics_response = (
        client.get(
            "/metrics"
        )
    )

    metrics = (
        metrics_response.text
    )

    assert (
        'path="/jobs/{job_id}"'
        in metrics
    )