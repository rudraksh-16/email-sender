"""Business logic + side-effect modules.

Routers stay thin: validate input, call a service, return a DTO. Anything
involving the network, filesystem, or non-trivial logic belongs here so it
can be unit-tested without spinning up FastAPI.
"""
