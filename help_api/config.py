"""Settings for the Help chatbot — a deliberately separate process from api/.

Cognee's own config (`get_base_config()`, `get_embedding_config()`) is a
process-wide `@lru_cache()` singleton with no per-dataset scoping — setting it
once mutates it for every call in that process. Running the docs graph's NIM
config in the same process as the live scam-detection API would race with
concurrent /report requests (and risks a 384 vs 1024 dim mismatch). Giving it
its own process/port sidesteps that entirely: each process gets its own
Cognee singleton, isolated by the OS, not by convention.
"""
from __future__ import annotations

import socket
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Same IPv4-only fix as api/config.py — this network's IPv6 SLAAC addresses
# aren't routed, so AAAA-resolved hosts (NIM included) hang in SYN_SENT
# without it.
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if family == socket.AF_UNSPEC:
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_only_getaddrinfo


class HelpSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    help_api_host: str = "127.0.0.1"
    help_api_port: int = 8010
    help_web_origin: str = "http://localhost:5173"

    # Wholly separate from api/'s ./.antibody_data — different Cognee project,
    # different SQLite/LanceDB/Kuzu files on disk.
    help_data_dir: Path = Path("./.antibody_help_data")
    help_dataset_name: str = "antibody_help_docs"

    # Prefixed so these never collide with (or accidentally enable) the main
    # api's own LLM_PROVIDER/LLM_API_KEY, which stay off on purpose there.
    help_llm_provider: str = "openai"
    help_llm_model: str = "gpt-4o-mini"
    help_llm_endpoint: str = ""
    help_llm_api_key: str = ""
    help_nvidia_nim_api_key: str = ""  # litellm's nvidia_nim provider reads this name directly

    help_embedding_provider: str = "fastembed"
    help_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    help_embedding_dimensions: int = 384
    help_embedding_endpoint: str = ""
    help_embedding_api_key: str = ""

    @property
    def has_llm(self) -> bool:
        return bool(self.help_llm_api_key)

    def export_cognee_env(self) -> None:
        """Push settings into THIS process's env so Cognee/litellm pick them
        up. Never touches the main api process — separate OS process."""
        import os

        self.help_data_dir.mkdir(parents=True, exist_ok=True)
        env = {
            "LLM_PROVIDER": self.help_llm_provider,
            "LLM_MODEL": self.help_llm_model,
            "LLM_API_KEY": self.help_llm_api_key,
            "NVIDIA_NIM_API_KEY": self.help_nvidia_nim_api_key,
            "EMBEDDING_PROVIDER": self.help_embedding_provider,
            "EMBEDDING_MODEL": self.help_embedding_model,
            "EMBEDDING_DIMENSIONS": str(self.help_embedding_dimensions),
            "AUTO_FEEDBACK": "false",
            "COGNEE_SKIP_CONNECTION_TEST": "true",
            "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        }
        if self.help_llm_endpoint:
            env["LLM_ENDPOINT"] = self.help_llm_endpoint
        if self.help_embedding_endpoint:
            env["EMBEDDING_ENDPOINT"] = self.help_embedding_endpoint
        if self.help_embedding_api_key:
            env["EMBEDDING_API_KEY"] = self.help_embedding_api_key
        for k, v in env.items():
            if v:
                os.environ.setdefault(k, v)


@lru_cache
def get_help_settings() -> HelpSettings:
    return HelpSettings()


help_settings = get_help_settings()
