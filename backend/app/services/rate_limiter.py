"""Token-bucket rate limiter, keyed by SMTP account id.

In-memory, single-process (safe because the desktop app runs exactly one
uvicorn worker). Two buckets per account: per-minute and per-hour. Buckets
reset on app restart — documented as a known limit.

Planned API:
    async def acquire(account_id: str, capacity_per_min: int, capacity_per_hour: int) -> None
"""
