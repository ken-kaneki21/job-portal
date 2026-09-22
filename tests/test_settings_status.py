from fastapi.testclient import TestClient

from jobintel.api import app


def test_settings_status_is_safe_and_structured(
    monkeypatch,
):
    monkeypatch.delenv(
        "RESEND_API_KEY",
        raising=False,
    )
    monkeypatch.delenv(
        "NOTIFICATION_FROM_EMAIL",
        raising=False,
    )
    monkeypatch.delenv(
        "NOTIFICATION_TO_EMAIL",
        raising=False,
    )

    client = TestClient(app)

    response = client.get("/settings/status")

    assert response.status_code == 200

    payload = response.json()

    assert payload["privacy"]["review_before_submit"] is True
    assert payload["privacy"]["auto_submit_enabled"] is False
    assert payload["integrations"]["resend"] is False
