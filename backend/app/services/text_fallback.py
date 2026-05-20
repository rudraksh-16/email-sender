"""html2text fallback so every multipart/alternative carries a text/plain part.

Plain-text clients (mutt, some Apple Watch previews, spam filters scoring
for text part presence) read this. Stripping links/images and re-flowing
paragraphs is good enough.

Planned API:
    def to_text(html: str) -> str
"""
