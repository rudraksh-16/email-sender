from __future__ import annotations

from pydantic import BaseModel


class VerifyRowResult(BaseModel):
    index: int
    email: str  # original value from the list
    normalized: str | None
    verdict: str  # "valid" | "invalid" | "duplicate"
    reason: str | None
    data: dict[str, str]  # merge fields (everything except email), for re-sending kept rows


class VerifySummary(BaseModel):
    total: int
    valid: int
    invalid: int
    duplicate: int


class VerifyReport(BaseModel):
    summary: VerifySummary
    rows: list[VerifyRowResult]
