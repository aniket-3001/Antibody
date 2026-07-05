"""A small typed error hierarchy for the API.

Routers raise these instead of bare ``fastapi.HTTPException`` so that:

- call sites read as intent (``raise EmptyReportError()``), not status codes;
- every error renders through one handler into a single stable JSON envelope
  (see ``error_handlers.py``), so clients get a consistent shape to parse;
- the type name (e.g. ``ReportNotFoundError``) travels to the client as the
  machine-readable ``error`` field without leaking internals.

The hierarchy is intentionally tiny — Antibody is a single-user service, not a
multi-tenant SaaS, so it carries exactly the four failure modes its endpoints
actually produce, plus a base class the global handler can special-case.
"""
from __future__ import annotations

from fastapi import status


class AntibodyError(Exception):
    """Base class for every expected, client-facing error.

    ``status_code`` and ``code`` are class attributes so subclasses read as pure
    declarations; ``detail`` is the human-readable message shown to the client.
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "antibody_error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.__doc__ or "Request could not be processed."
        super().__init__(self.detail)


class BadRequestError(AntibodyError):
    """The request was malformed or semantically empty."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"


class EmptyReportError(BadRequestError):
    """A report was submitted with no assessable text."""

    code = "empty_report"

    def __init__(self, detail: str = "Empty report — nothing to assess.") -> None:
        super().__init__(detail)


class ReportNotFoundError(AntibodyError):
    """The referenced report id does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "report_not_found"

    def __init__(self, detail: str = "Report not found.") -> None:
        super().__init__(detail)


class UnsupportedOutcomeError(BadRequestError):
    """An outcome value outside the accepted set was supplied."""

    code = "unsupported_outcome"
