from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    # Don't actually run the sender for queued campaigns in tests.
    from app.routers import campaigns as campaigns_router

    async def _noop(_campaign_id: str) -> None:
        return None

    monkeypatch.setattr(campaigns_router.campaign_runner, "run_campaign", _noop)
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c
    get_settings.cache_clear()


def _make_account(client: TestClient) -> str:
    r = client.post(
        "/api/smtp-accounts",
        json={
            "name": "Test",
            "host": "smtp.example.com",
            "port": 587,
            "from_email": "sender@example.com",
            "password": "secret",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_campaign(client: TestClient, account_id: str) -> str:
    r = client.post(
        "/api/campaigns",
        json={
            "name": "Launch",
            "subject": "Hi {{name}}",
            "body_html": "<p>Hello {{name}}</p>",
            "smtp_account_id": account_id,
            "recipients": [
                {"email": "a@example.com", "data": {"name": "A"}},
                {"email": "b@example.com", "data": {"name": "B"}},
            ],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_duplicate_clones_all_recipients_and_keeps_source(client: TestClient) -> None:
    account_id = _make_account(client)
    src_id = _make_campaign(client, account_id)

    r = client.post(f"/api/campaigns/{src_id}/duplicate", json={"recipients": "all"})
    assert r.status_code == 201, r.text
    new = r.json()

    assert new["id"] != src_id
    assert new["status"] == "queued"
    assert new["total"] == 2
    assert new["name"] == "Launch (resend)"
    assert new["subject"] == "Hi {{name}}"
    assert new["smtp_account_id"] == account_id

    # Source campaign untouched.
    src = client.get(f"/api/campaigns/{src_id}").json()
    assert src["total"] == 2
    assert src["name"] == "Launch"


def test_duplicate_custom_name(client: TestClient) -> None:
    account_id = _make_account(client)
    src_id = _make_campaign(client, account_id)

    r = client.post(
        f"/api/campaigns/{src_id}/duplicate",
        json={"recipients": "all", "name": "Second wave"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Second wave"


def test_duplicate_failed_scope_with_no_failures_rejected(client: TestClient) -> None:
    account_id = _make_account(client)
    src_id = _make_campaign(client, account_id)

    # All logs are still queued (runner is a no-op), so "failed" scope is empty.
    r = client.post(f"/api/campaigns/{src_id}/duplicate", json={"recipients": "failed"})
    assert r.status_code in (400, 422), r.text


def test_duplicate_sent_scope_clones_only_sent(client: TestClient) -> None:
    from sqlalchemy import select

    from app.db import get_session_factory
    from app.models import EmailLog, EmailLogStatus

    account_id = _make_account(client)
    src_id = _make_campaign(client, account_id)

    async def _mark_one_sent() -> None:
        Session = get_session_factory()
        async with Session() as session:
            logs = (
                (await session.execute(select(EmailLog).where(EmailLog.campaign_id == src_id)))
                .scalars()
                .all()
            )
            logs[0].status = EmailLogStatus.sent
            await session.commit()

    asyncio.run(_mark_one_sent())

    r = client.post(f"/api/campaigns/{src_id}/duplicate", json={"recipients": "sent"})
    assert r.status_code == 201, r.text
    assert r.json()["total"] == 1


def test_delete_running_campaign_rejected(client: TestClient) -> None:
    from sqlalchemy import select

    from app.db import get_session_factory
    from app.models import Campaign, CampaignStatus

    account_id = _make_account(client)
    src_id = _make_campaign(client, account_id)

    async def _mark_running() -> None:
        Session = get_session_factory()
        async with Session() as session:
            c = (
                await session.execute(select(Campaign).where(Campaign.id == src_id))
            ).scalar_one()
            c.status = CampaignStatus.running
            await session.commit()

    asyncio.run(_mark_running())

    r = client.delete(f"/api/campaigns/{src_id}")
    assert r.status_code in (400, 422), r.text


def test_delete_campaign_removes_it(client: TestClient) -> None:
    account_id = _make_account(client)
    src_id = _make_campaign(client, account_id)

    # Created campaign is "queued"; flip to a terminal state so delete is allowed.
    from sqlalchemy import select

    from app.db import get_session_factory
    from app.models import Campaign, CampaignStatus

    async def _mark_done() -> None:
        Session = get_session_factory()
        async with Session() as session:
            c = (
                await session.execute(select(Campaign).where(Campaign.id == src_id))
            ).scalar_one()
            c.status = CampaignStatus.done
            await session.commit()

    asyncio.run(_mark_done())

    r = client.delete(f"/api/campaigns/{src_id}")
    assert r.status_code == 204, r.text
    assert client.get(f"/api/campaigns/{src_id}").status_code == 404


def test_delete_missing_campaign_404(client: TestClient) -> None:
    r = client.delete("/api/campaigns/does-not-exist")
    assert r.status_code == 404, r.text
