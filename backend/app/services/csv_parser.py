"""Stream-parse uploaded CSVs into merge dicts."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator

from app.config import get_settings
from app.utils.email_validate import normalise_email
from app.utils.errors import ValidationError


def parse(stream: io.TextIOBase) -> Iterator[dict[str, str]]:
    """Yield one dict per row.

    Requires an ``email`` column. Enforces the row cap from settings.
    """
    settings = get_settings()
    reader = csv.DictReader(stream)
    if not reader.fieldnames or "email" not in {f.lower() for f in reader.fieldnames}:
        raise ValidationError("CSV must include an 'email' column")

    # Normalise field names to lowercase so templates can use lowercased keys.
    fieldnames = [f.lower() for f in reader.fieldnames]

    for i, raw in enumerate(reader):
        if i >= settings.CSV_ROW_CAP:
            raise ValidationError(f"CSV exceeds row cap ({settings.CSV_ROW_CAP})")
        row = {fieldnames[j]: (v or "").strip() for j, (_, v) in enumerate(raw.items())}
        try:
            row["email"] = normalise_email(row["email"])
        except ValidationError as exc:
            raise ValidationError(f"Row {i + 2}: {exc.message}") from exc
        yield row


def parse_bytes(data: bytes, encoding: str = "utf-8") -> list[dict[str, str]]:
    return list(parse(io.StringIO(data.decode(encoding))))


def parse_lenient(stream: io.TextIOBase) -> list[dict[str, str]]:
    """Parse rows without validating individual emails.

    Structural problems (no ``email`` column, row cap exceeded) still raise.
    Per-row email validity is left to ``email_verifier`` so the caller can
    surface a per-row report instead of aborting on the first bad address.
    """
    settings = get_settings()
    reader = csv.DictReader(stream)
    if not reader.fieldnames or "email" not in {f.lower() for f in reader.fieldnames}:
        raise ValidationError("CSV must include an 'email' column")

    fieldnames = [f.lower() for f in reader.fieldnames]
    rows: list[dict[str, str]] = []
    for i, raw in enumerate(reader):
        if i >= settings.CSV_ROW_CAP:
            raise ValidationError(f"CSV exceeds row cap ({settings.CSV_ROW_CAP})")
        rows.append({fieldnames[j]: (v or "").strip() for j, (_, v) in enumerate(raw.items())})
    return rows


def parse_lenient_bytes(data: bytes, encoding: str = "utf-8") -> list[dict[str, str]]:
    return parse_lenient(io.StringIO(data.decode(encoding)))
