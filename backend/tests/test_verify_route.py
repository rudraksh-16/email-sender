from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    # MX off so the test stays offline and deterministic.
    monkeypatch.setenv("EMAIL_APP_VERIFY_CHECK_MX", "false")
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c
    get_settings.cache_clear()


def test_verify_csv_returns_per_row_report(client: TestClient) -> None:
    csv_bytes = b"email,name\ngood@example.com,A\nnot-an-email,B\ngood@example.com,C\n"
    r = client.post(
        "/api/verify",
        files={"file": ("list.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()

    assert body["summary"] == {"total": 3, "valid": 1, "invalid": 1, "duplicate": 1}
    verdicts = [row["verdict"] for row in body["rows"]]
    assert verdicts == ["valid", "invalid", "duplicate"]
    # Merge data is preserved so the client can re-send kept rows.
    assert body["rows"][0]["data"] == {"name": "A"}


def test_verify_rejects_missing_email_column(client: TestClient) -> None:
    r = client.post(
        "/api/verify",
        files={"file": ("list.csv", b"name,city\nA,X\n", "text/csv")},
    )
    assert r.status_code == 422
