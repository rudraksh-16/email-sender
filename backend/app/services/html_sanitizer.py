"""bleach.clean allowlist applied AFTER Jinja render, BEFORE SMTP send.

Sanitising post-render means template authors can't smuggle ``<script>`` via
merge data. Allowlist covers the tags TipTap actually emits: p, br, strong,
em, u, s, a (href + rel), ul, ol, li, blockquote, code, pre, h1-h4, img
(src, alt, width, height), hr.

Planned API:
    def sanitize(html: str) -> str
"""
