"""Typed settings for Antibody. Single source of env config.

Antibody runs Cognee zero-config self-hosted (SQLite + LanceDB + Kuzu): we do
NOT set DB_PROVIDER=postgres, so Cognee falls back to its embedded stores. The
only external dependency is an LLM key for cognify()/GRAPH_COMPLETION. Without
one, the deterministic + semantic matching layer still produces a correct
verdict band (see api/verdict/engine.py) — Cognee is the star, not a crutch.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_env: str = "dev"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    web_origin: str = "http://localhost:5173"

    # Where Antibody keeps its ops DB (PII-bearing reporter table + report log +
    # local semantic index). Kept separate from Cognee's de-identified graph
    # (spec §10: GDPR is a normal DB delete here, never graph surgery).
    data_dir: Path = Path("./.antibody_data")

    # The one shared global graph — herd immunity is the point (spec §12).
    dataset_name: str = "antibody_global"

    # --- LLM (OpenAI-compatible; read directly by Cognee from these env vars) ---
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_endpoint: str = ""
    llm_api_key: str = ""

    # --- Embeddings: local fastembed by default (no API key needed) ---
    embedding_provider: str = "fastembed"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    embedding_endpoint: str = ""
    embedding_api_key: str = ""

    # Confidence band thresholds (spec §6)
    band_confirmed: float = 0.85
    band_likely: float = 0.60
    band_suspicious: float = 0.35

    @property
    def has_llm(self) -> bool:
        return bool(self.llm_api_key)

    def export_cognee_env(self) -> None:
        """Push LLM/embedding config into the process env so Cognee picks it up.

        Cognee reads its own env vars via python-dotenv; we mirror our settings
        onto the names it expects. Called once before the first Cognee import.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        env = {
            "LLM_PROVIDER": self.llm_provider,
            "LLM_MODEL": self.llm_model,
            "LLM_API_KEY": self.llm_api_key,
            "EMBEDDING_PROVIDER": self.embedding_provider,
            "EMBEDDING_MODEL": self.embedding_model,
            "EMBEDDING_DIMENSIONS": str(self.embedding_dimensions),
            # Deterministic search + fast startup (spec/meetgraph parity)
            "AUTO_FEEDBACK": "false",
            "COGNEE_SKIP_CONNECTION_TEST": "true",
        }
        if self.llm_endpoint:
            env["LLM_ENDPOINT"] = self.llm_endpoint
        if self.embedding_endpoint:
            env["EMBEDDING_ENDPOINT"] = self.embedding_endpoint
        if self.embedding_api_key:
            env["EMBEDDING_API_KEY"] = self.embedding_api_key
        for k, v in env.items():
            if v:
                os.environ.setdefault(k, v)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
