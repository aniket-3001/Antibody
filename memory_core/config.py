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


_REQUIRED_MODE_A_VARS = ("LLM_PROVIDER", "LLM_API_KEY", "EMBEDDING_PROVIDER")
_PLACEHOLDER_MARKERS = ("PASTE_", "YOUR_", "CHANGE_ME")


def get_provider() -> MemoryProvider:
    """Resolve the active MemoryProvider from environment configuration.

    Raises ConfigurationError immediately for an unrecognized mode, or for
    Mode A with a missing/placeholder required env var, rather than
    surfacing a confusing failure deep inside ingest()/recall() later —
    see design §6.3's rationale for why ConfigurationError is fail-fast and
    separated from ProviderError.

    This closes the exception-taxonomy gap named in Docs/PROJECT_HEALTH.md
    §6 (ConfigurationError previously only fired for a bad mode name).
    Note what it does *not* cover: Milestone 1's billing failure (a valid
    key, insufficient credits) is not detectable at config time — that is
    correctly a runtime ProviderError, not a configuration problem. This
    check only catches "the env var is missing or still a placeholder,"
    not "the credentials are valid and funded."
    """
    mode = os.environ.get(_MODE_ENV_VAR, "local").strip().lower()
    if mode in ("local", "mode_a", "a"):
        _validate_mode_a_env()
        return ModeAProvider()
    if mode in ("cloud", "mode_b", "b"):
        return ModeBProvider()
    raise ConfigurationError(
        f"{_MODE_ENV_VAR}={mode!r} is not recognized. Expected 'local' or 'cloud'."
    )


def _validate_mode_a_env() -> None:
    missing = []
    for var in _REQUIRED_MODE_A_VARS:
        value = os.environ.get(var, "").strip()
        if not value or any(marker in value.upper() for marker in _PLACEHOLDER_MARKERS):
            missing.append(var)
    if missing:
        raise ConfigurationError(
            f"Mode A requires {_REQUIRED_MODE_A_VARS} to be set in .env; "
            f"missing or still a placeholder: {missing}. See .env.example."
        )
