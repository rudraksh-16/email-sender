"""aiosmtplib wrapper.

Connects (STARTTLS or implicit SSL), authenticates, builds an
``email.message.EmailMessage`` with multipart/alternative + attachments,
and sends. Raises ``SmtpSendError`` on any failure; retries are the caller's
responsibility (campaign_runner).

Planned API:
    async def send(account: SmtpAccount, message: EmailMessage) -> SmtpSendResult
    async def test_connection(account: SmtpAccount) -> None
"""
