"""Stream-parse uploaded CSVs into merge dicts.

Streamed (never buffers the whole file in memory), enforces a 50_000 row cap,
validates that an ``email`` column exists. Returns per-row dicts ready to feed
into ``mail_merge.render``.

Planned API:
    def parse(stream: IO[bytes], *, encoding: str = "utf-8")
        -> Iterator[dict[str, str]]
"""
