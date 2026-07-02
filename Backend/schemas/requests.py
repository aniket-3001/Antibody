"""Pydantic request models.

Spec reference: BACKEND_API_SPEC.md §5.3 (RecallRequest), §5.4 (ForgetRequest).

Remember/Improve use multipart/form-data (FastAPI Form + File fields) rather
than Pydantic models — see their route handlers for validation logic.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, field_validator

from Backend.config import MAX_QUERY_LENGTH, SOURCE_ID_PATTERN


class RecallRequest(BaseModel):
    """POST /api/v1/recall request body (spec §5.3)."""

    query: str
    strategy: Literal["relationship", "contradiction", "gap_analysis", "factual"] | None = None

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("query must not be empty after stripping whitespace")
        if len(stripped) > MAX_QUERY_LENGTH:
            raise ValueError(f"query must not exceed {MAX_QUERY_LENGTH} characters")
        return stripped


class ForgetRequest(BaseModel):
    """POST /api/v1/forget request body (spec §5.4)."""

    source_id: str

    @field_validator("source_id")
    @classmethod
    def source_id_format(cls, v: str) -> str:
        if not re.match(SOURCE_ID_PATTERN, v):
            raise ValueError(
                "source_id must be a 32-character lowercase hex string "
                "(the format returned by /remember or /sources)"
            )
        return v
