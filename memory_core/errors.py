"""Exception hierarchy for memory_core.

Design reference: Docs/MEMORY_CORE_DESIGN.md §6.

Governing rule (see §6.2): raise for a failure to complete the requested
operation; return normally for a legitimate empty/negative result (no
evidence found, nothing to delete, an empty project). Callers should be
able to catch MemoryCoreError broadly and any specific subtype narrowly.
"""

from __future__ import annotations


class MemoryCoreError(Exception):
    """Base class for every exception memory_core raises.

    No memory_core function ever lets a raw Cognee/provider-SDK exception
    cross the module boundary uncaught — see design §2's intro and §1.1's
    provider-opacity goal.
    """


class ConfigurationError(MemoryCoreError):
    """The active provider is misconfigured (missing key, unreachable).

    Raised eagerly by config.py at provider-resolution time, not deep
    inside an ingest/recall call — see design §6.3 for why this is split
    out from ProviderError.
    """


class OntologyError(MemoryCoreError):
    """The ontology (vocabulary or OWL projection) failed to load or validate."""


class ProviderError(MemoryCoreError):
    """An LLM/embedding/DB call failed after the provider's own retries were exhausted."""


class ExtractionError(MemoryCoreError):
    """cognify() (or the active provider's equivalent) raised — a hard pipeline fault.

    Narrowly scoped per design §6.3: "succeeded but extracted few/no
    entities" is NOT this exception — that is reported as
    IngestResult(status="degraded"), not raised.
    """


class RecallError(MemoryCoreError):
    """The recall pipeline itself failed to execute.

    Never raised for an honest "no evidence found" answer — see design
    §2.3 and §6.2's governing rule.
    """


class CapabilityUnavailableError(MemoryCoreError):
    """The requested operation needs a capability the active provider doesn't have.

    E.g. get_graph() when the active provider's capabilities().
    supports_deterministic_evidence is False. See design §4.5 and §6.3 for
    why this exists as its own type rather than a silent empty result.
    """
