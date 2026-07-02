"""Provider/mode resolution from environment.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3 ("config.py"), §4.4.

The single place that decides which MemoryProvider implementation is
active. Selecting Mode A vs. Mode B is one env var here — never a code
change at any call site (design §4.4).
"""

from __future__ import annotations

import os

from memory_core.errors import ConfigurationError
from memory_core.providers.base import MemoryProvider
from memory_core.providers.mode_a import ModeAProvider
from memory_core.providers.mode_b import ModeBProvider

_MODE_ENV_VAR = "MEMORY_CORE_MODE"


def get_provider() -> MemoryProvider:
    """Resolve the active MemoryProvider from environment configuration.

    Raises ConfigurationError immediately for an unrecognized mode, rather
    than surfacing a confusing failure deep inside ingest()/recall() later
    — see design §6.3's rationale for why ConfigurationError is fail-fast
    and separated from ProviderError.

    Milestone 2.2 TODO: validate Mode A's required env vars
    (LLM_PROVIDER/LLM_API_KEY/EMBEDDING_PROVIDER, per ARCHITECTURE.md
    §9.1) here too, not just the mode name — this is the exact failure
    class Milestone 1's billing error fell into (Docs/PROGRESS.md).
    """
    mode = os.environ.get(_MODE_ENV_VAR, "local").strip().lower()
    if mode in ("local", "mode_a", "a"):
        return ModeAProvider()
    if mode in ("cloud", "mode_b", "b"):
        return ModeBProvider()
    raise ConfigurationError(
        f"{_MODE_ENV_VAR}={mode!r} is not recognized. Expected 'local' or 'cloud'."
    )
