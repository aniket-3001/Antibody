"""MemoryAPIError and error code constants.

Spec reference: BACKEND_API_SPEC.md §2 (Global Error Envelope) and §3
(Exception Mapping).  Every HTTP error the backend returns goes through
MemoryAPIError → global exception handler → the standard JSON envelope:

    {"error": {"code": "...", "message": "...", "detail": "..."}}
"""

from __future__ import annotations


class MemoryAPIError(Exception):
    """Raised by service functions; serialised by the global exception handler."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        detail: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)


class ErrorCode:
    """Machine-readable error code constants (spec §3)."""

    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    ONTOLOGY_ERROR = "ONTOLOGY_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    RECALL_FAILED = "RECALL_FAILED"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
