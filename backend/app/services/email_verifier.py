"""Per-email pre-flight verification: syntax, dedupe, and MX (deliverability).

Pure orchestration over ``email-validator``. Returns one verdict per input row
without raising — the caller surfaces the list to the user before sending.
MX checking is delegated to email-validator's ``check_deliverability`` (which
bundles dnspython); a per-call caching resolver avoids re-resolving repeated
domains.
"""

from __future__ import annotations

from dataclasses import dataclass

from email_validator import EmailNotValidError, caching_resolver, validate_email


@dataclass
class RowVerdict:
    index: int
    email: str  # original, untrimmed
    normalized: str | None
    verdict: str  # "valid" | "invalid" | "duplicate"
    reason: str | None


def verify_rows(emails: list[str], *, check_mx: bool = True) -> list[RowVerdict]:
    resolver = caching_resolver() if check_mx else None
    seen: set[str] = set()
    out: list[RowVerdict] = []

    for i, raw in enumerate(emails):
        addr = (raw or "").strip()
        if not addr:
            out.append(RowVerdict(i, raw, None, "invalid", "Empty email"))
            continue
        try:
            info = validate_email(addr, check_deliverability=check_mx, dns_resolver=resolver)
        except EmailNotValidError as exc:
            out.append(RowVerdict(i, raw, None, "invalid", str(exc)))
            continue

        norm = info.normalized
        key = norm.lower()
        if key in seen:
            out.append(RowVerdict(i, raw, norm, "duplicate", "Duplicate of an earlier row"))
            continue
        seen.add(key)
        out.append(RowVerdict(i, raw, norm, "valid", None))

    return out
