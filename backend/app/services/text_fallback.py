"""html2text fallback."""

from __future__ import annotations

import html2text


def to_text(html: str) -> str:
    h = html2text.HTML2Text()
    h.body_width = 0  # don't hard-wrap
    h.ignore_images = False
    h.ignore_links = False
    return h.handle(html).strip()
