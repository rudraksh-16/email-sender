"""bleach allowlist applied AFTER Jinja render."""
from __future__ import annotations

import bleach

_ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        "a", "b", "blockquote", "br", "code", "div", "em", "h1", "h2", "h3",
        "h4", "hr", "i", "img", "li", "ol", "p", "pre", "s", "span", "strong",
        "u", "ul",
    }
)
_ALLOWED_ATTRS: dict[str, list[str]] = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "width", "height", "title"],
    "span": ["style"],
    "div": ["style"],
    "p": ["style"],
}
_ALLOWED_PROTOCOLS: list[str] = ["http", "https", "mailto", "data"]


def sanitize(html: str) -> str:
    cleaned = bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
    # Force noopener/noreferrer on outbound links.
    return bleach.linkify(
        cleaned,
        callbacks=[lambda attrs, new: {**attrs, (None, "rel"): "noopener noreferrer"}],
        skip_tags=["pre", "code"],
    )
