"""Backend configuration constants.

Spec reference: BACKEND_API_SPEC.md §1.1 (project_id hard-coded to "demo"),
§5.1 (file size limits, content length, title length), §5.3 (query limits),
§5.4 (source_id format).

Do not expose PROJECT_ID in the API surface — it is a server-side constant
for the hackathon MVP.  See spec §7 Q2 for the design decision.
"""

from __future__ import annotations

# ── Project ───────────────────────────────────────────────────────────────────
PROJECT_ID: str = "demo"

# ── API version ───────────────────────────────────────────────────────────────
VERSION: str = "1.0.0"

# ── File upload limits (spec §5.1) ────────────────────────────────────────────
FILE_SIZE_LIMIT_MB: int = 20
FILE_SIZE_LIMIT_BYTES: int = FILE_SIZE_LIMIT_MB * 1024 * 1024

# ── Content limits (spec §5.1) ────────────────────────────────────────────────
MAX_CONTENT_LENGTH: int = 500_000   # characters
MAX_TITLE_LENGTH: int = 255         # characters
MAX_ACTIVE_HYPOTHESES: int = 5
MAX_HYPOTHESIS_LENGTH: int = 1_000  # characters per hypothesis

# ── Query limits (spec §5.3) ──────────────────────────────────────────────────
MAX_QUERY_LENGTH: int = 2_000       # characters

# ── Valid source types (spec §5.1) ────────────────────────────────────────────
VALID_CONTENT_TYPES: frozenset[str] = frozenset({"pdf", "text", "markdown", "url"})

# ── source_id format (spec §5.4) ─────────────────────────────────────────────
SOURCE_ID_PATTERN: str = r"^[0-9a-f]{32}$"
