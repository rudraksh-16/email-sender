"""Thin wrapper around `email-validator`.

Activated with the send/contacts slice. Returns the normalised address and
raises ``ValidationError`` on malformed input. ``check_deliverability=False``
is used since the user is sending, not registering.
"""
