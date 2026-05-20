"""On-disk attachment storage under user_data_dir/attachments.

Files are stored under UUID names; the original filename is preserved in the
DB and only used for the Content-Disposition header on send. MIME is sniffed
with python-magic and checked against the allowlist before persisting.

Planned API:
    async def store(stream: IO[bytes], *, filename: str, declared_mime: str) -> Attachment
    async def open_blob(attachment: Attachment) -> IO[bytes]
    async def delete(attachment: Attachment) -> None
"""
