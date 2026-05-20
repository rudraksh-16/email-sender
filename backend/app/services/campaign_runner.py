"""Bulk-send orchestrator.

Scheduled by the campaigns router via FastAPI BackgroundTasks. Owns the
end-to-end lifecycle:

    1. Pull queued EmailLog rows for a campaign in batches.
    2. For each row:
        - acquire rate-limit tokens
        - render subject + body (mail_merge)
        - sanitise body (html_sanitizer) and derive text part (text_fallback)
        - call smtp_sender.send
        - mark row sent / failed, increment counters
    3. Mark the Campaign done / failed when the queue drains.

Uses its own AsyncSession (not the request session) since the request has
returned long before the task finishes.
"""
