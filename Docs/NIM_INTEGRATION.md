# NIM (NVIDIA Inference Microservices) API Integration

This branch integrates the NVIDIA NIM API as the LLM and embedding provider,
replacing the previous Anthropic-based setup.

## Configuration

Copy `.env.example` to `.env` and fill in your NVIDIA NIM API key from
[build.nvidia.com](https://build.nvidia.com).

```
LLM_PROVIDER=custom
NVIDIA_NIM_API_KEY=your-nvapi-key-here
LLM_API_KEY=your-nvapi-key-here
LLM_MODEL=nvidia_nim/meta/llama-4-maverick-17b-128e-instruct
EMBEDDING_PROVIDER=litellm
EMBEDDING_MODEL=nvidia_nim/nvidia/nv-embedqa-e5-v5
EMBEDDING_DIMENSIONS=1024
EMBEDDING_API_KEY=your-nvapi-key-here
COGNEE_SKIP_CONNECTION_TEST=true
```

## Models Used

| Role | Model | Notes |
|------|-------|-------|
| LLM | `meta/llama-3.3-70b-instruct` | 128k context, free tier via NIM |
| Embeddings | `nvidia/nv-embedqa-e5-v5` | 1024-dim asymmetric embedding model |

## Known Patches Applied

The `cognee` library's `LiteLLMEmbeddingEngine` was patched (in-place in
`.venv/`) to support NVIDIA NIM's embedding API requirements:

1. **Suppressed `dimensions` kwarg** — NIM embedding models do not accept this
   parameter (they have a fixed output size).
2. **Injected `input_type=passage`** — NIM's `nv-embedqa-e5-v5` is an
   asymmetric model that requires specifying whether the input is a `query`
   or a `passage`. Cognee always embeds documents during indexing, so
   `passage` is always correct here.

3. **Patched `LanceDBAdapter.py` for search queries** — Since NIM's `nv-embedqa-e5-v5` is asymmetric, queries must be embedded with `input_type="query"`. We patched `LanceDBAdapter.search` to pass `input_type="query"` when making inference embedding calls during vector search.

These patches apply only when `nvidia_nim/` is detected in the model string,
so other providers are unaffected.

## Test Results

All Milestone 2.2 criteria **PASS** with NIM as the backend:

```
Overall: PASS
- memory_core public API installs/imports/runs   PASS
- Sources ingested via ingest()                   PASS
- Graph created (get_graph())                     PASS
- Tier-1 relationships present                    PASS
- ≥ 1 correct CONTRADICTS edge (find_evidence())  PASS
- find_evidence() required zero LLM calls         PASS
- recall() produced a natural-language answer     PASS
- recall() attached an evidence_graph             PASS
- No direct `import cognee` in this script        PASS
- All public API methods exercised                PASS
```
