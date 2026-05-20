"""Jinja2 sandboxed renderer for subject + body.

Uses ``SandboxedEnvironment`` with ``StrictUndefined`` so template authors
get loud errors on typos rather than silent empty strings. Custom filters
(date, default_if_blank, etc.) registered here.

Planned API:
    def render(template: str, data: Mapping[str, Any]) -> str
"""
