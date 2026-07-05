"""Shared fixtures for the API tests.

The ``client`` fixture boots the whole FastAPI app (ops store + seed graph +
semantic index) once per session, forcing the no-LLM deterministic/fastembed
fallback path — the exact configuration CI and a keyless judge run under. Env is
set before ``api.main`` is first imported so the cached ``Settings`` pick it up.
"""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def client():
    import tempfile

    data_dir = tempfile.mkdtemp(prefix="antibody_test_")
    os.environ["DATA_DIR"] = data_dir
    # Force the deterministic/fastembed fallback regardless of a local .env.
    os.environ["LLM_API_KEY"] = ""
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["EMBEDDING_API_KEY"] = ""
    os.environ["EMBEDDING_PROVIDER"] = "fastembed"

    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as c:
        yield c
