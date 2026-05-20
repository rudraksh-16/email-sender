"""SMTP account DTOs.

Planned shapes:
    SmtpAccountCreate / SmtpAccountUpdate / SmtpAccountRead
    SmtpAccountTestRequest / SmtpAccountTestResult

``password`` is write-only on Create/Update; no Read DTO ever exposes it.
"""
