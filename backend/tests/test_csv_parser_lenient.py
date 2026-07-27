from __future__ import annotations

import io

import pytest

from app.services.csv_parser import parse_lenient
from app.utils.errors import ValidationError


def _rows(text: str) -> list[dict[str, str]]:
    return parse_lenient(io.StringIO(text))


def test_keeps_malformed_emails_instead_of_raising() -> None:
    rows = _rows("email,name\ngood@example.com,A\nnot-an-email,B\n")
    assert [r["email"] for r in rows] == ["good@example.com", "not-an-email"]
    assert rows[1]["name"] == "B"


def test_missing_email_column_raises() -> None:
    with pytest.raises(ValidationError):
        _rows("name,city\nA,X\n")


def test_lowercases_headers_and_strips_values() -> None:
    rows = _rows("Email,Name\n  bob@example.com ,  Bob \n")
    assert rows[0] == {"email": "bob@example.com", "name": "Bob"}
