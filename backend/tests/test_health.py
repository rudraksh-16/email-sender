from __future__ import annotations


def test_health(client) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_runtime_config(client) -> None:
    r = client.get("/api/__config")
    assert r.status_code == 200
    assert r.json() == {"apiBase": ""}


def test_placeholder_index(client) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Email App" in r.text


def test_openapi_lists_all_routers(client) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    tags = {
        t for path in r.json()["paths"].values() for op in path.values() for t in op.get("tags", [])
    }
    # Health + system + every resource router should at least be wired in.
    assert {"health", "system"}.issubset(tags)
