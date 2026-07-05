"""Cross-cutting infrastructure shared by every layer of the API.

Kept deliberately dependency-light and framework-agnostic where possible so the
verdict/memory/intake packages never have to import FastAPI just to log or raise
a typed error. Three concerns live here:

- ``logging``        — structured logs stamped with a per-request correlation id
- ``exceptions``     — a small typed error hierarchy the routers raise
- ``error_handlers`` — one place that renders those errors as a stable JSON shape
"""
