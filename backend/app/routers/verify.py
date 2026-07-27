"""Pre-flight list verification: upload a recipient CSV, get a per-row report.

Stateless — creates no campaign. The client reviews the report, drops bad rows,
then posts the kept rows to ``/campaigns`` (the existing send pipeline).
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile

from app.config import get_settings
from app.schemas.verify import VerifyReport, VerifyRowResult, VerifySummary
from app.services import csv_parser, email_verifier
from app.utils.errors import ValidationError

router = APIRouter()


@router.post("", response_model=VerifyReport)
async def verify_csv(file: UploadFile) -> VerifyReport:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationError("Upload a .csv file")

    raw = await file.read()
    rows = csv_parser.parse_lenient_bytes(raw)

    verdicts = email_verifier.verify_rows(
        [r.get("email", "") for r in rows],
        check_mx=get_settings().VERIFY_CHECK_MX,
    )

    results: list[VerifyRowResult] = []
    counts = {"valid": 0, "invalid": 0, "duplicate": 0}
    for verdict, row in zip(verdicts, rows):
        counts[verdict.verdict] = counts.get(verdict.verdict, 0) + 1
        results.append(
            VerifyRowResult(
                index=verdict.index,
                email=verdict.email,
                normalized=verdict.normalized,
                verdict=verdict.verdict,
                reason=verdict.reason,
                data={k: v for k, v in row.items() if k != "email"},
            )
        )

    return VerifyReport(
        summary=VerifySummary(
            total=len(results),
            valid=counts["valid"],
            invalid=counts["invalid"],
            duplicate=counts["duplicate"],
        ),
        rows=results,
    )
