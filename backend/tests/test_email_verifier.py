from __future__ import annotations

from app.services.email_verifier import verify_rows


def test_valid_email_passes() -> None:
    rows = verify_rows(["alice@example.com"], check_mx=False)
    assert len(rows) == 1
    assert rows[0].verdict == "valid"
    assert rows[0].normalized == "alice@example.com"
    assert rows[0].reason is None


def test_malformed_email_is_invalid() -> None:
    rows = verify_rows(["not-an-email"], check_mx=False)
    assert rows[0].verdict == "invalid"
    assert rows[0].normalized is None
    assert rows[0].reason


def test_empty_email_is_invalid() -> None:
    rows = verify_rows(["", "   "], check_mx=False)
    assert [r.verdict for r in rows] == ["invalid", "invalid"]


def test_duplicate_is_flagged_after_first_valid() -> None:
    rows = verify_rows(["bob@example.com", "BOB@example.com"], check_mx=False)
    assert rows[0].verdict == "valid"
    assert rows[1].verdict == "duplicate"
    assert rows[1].reason


def test_index_and_original_preserved() -> None:
    rows = verify_rows(["  carol@example.com  "], check_mx=False)
    assert rows[0].index == 0
    assert rows[0].email == "  carol@example.com  "
    assert rows[0].normalized == "carol@example.com"
