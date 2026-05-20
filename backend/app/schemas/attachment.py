from __future__ import annotations

from app.schemas.common import TimestampedDTO


class AttachmentRead(TimestampedDTO):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    campaign_id: str | None = None
    template_id: str | None = None
