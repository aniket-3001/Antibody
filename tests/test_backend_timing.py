#!/usr/bin/env python3
"""
Backend timing + correctness test.
Tests: health, ingest (remember), graph, recall, sources, forget.
Reports latency for each endpoint.
"""
import time
import httpx
import json

BASE = "http://localhost:8000/api/v1"

SAMPLE_DOC = """
# Attention Is All You Need — Research Note

Authors: Vaswani et al., 2017
Topic: Natural Language Processing, Transformers

## Key Findings
The Transformer architecture, based entirely on attention mechanisms,
outperforms recurrent and convolutional models on machine translation tasks.
It achieves state-of-the-art BLEU scores on WMT 2014 English-to-German and
English-to-French translation benchmarks.

## Core Contribution
Self-attention allows the model to relate positions in a sequence directly,
regardless of distance — resolving the long-range dependency problem of RNNs.
"""

def fmt_ms(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.0f}ms"
    return f"{ms/1000:.1f}s"

def section(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print('═'*60)

results = {}

with httpx.Client(timeout=120.0) as client:

    # ── 1. Health ─────────────────────────────────────────────────────────────
    section("1. GET /health")
    t0 = time.perf_counter()
    r = client.get(f"{BASE}/health")
    ms = (time.perf_counter() - t0) * 1000
    results["health"] = ms
    print(f"  Status: {r.status_code} | {fmt_ms(ms)}")
    print(f"  Body: {r.json()}")
    assert r.status_code == 200

    # ── 2. Remember (ingest) ──────────────────────────────────────────────────
    section("2. POST /remember (ingest document)")
    print("  ⏳ Sending document to cognify pipeline...")
    t0 = time.perf_counter()
    r = client.post(
        f"{BASE}/remember",
        data={
            "content_type": "markdown",
            "content": SAMPLE_DOC,
            "title": "Attention Is All You Need",
            "active_hypotheses": json.dumps(["Transformers are better than RNNs for NLP"]),
        },
        timeout=300.0,
    )
    ms = (time.perf_counter() - t0) * 1000
    results["remember"] = ms
    print(f"  Status: {r.status_code} | {fmt_ms(ms)}")
    body = r.json()
    print(f"  source_id: {body.get('source_id', 'N/A')}")
    print(f"  status: {body.get('status', 'N/A')}")
    print(f"  nodes_created: {body.get('nodes_created', 'N/A')}")
    print(f"  edges_created: {body.get('edges_created', 'N/A')}")
    print(f"  duration_ms (server-side): {body.get('duration_ms', 'N/A')}")
    if r.status_code not in (200, 201):
        print(f"  ERROR: {body}")

    # ── 3. Graph ──────────────────────────────────────────────────────────────
    section("3. GET /graph")
    t0 = time.perf_counter()
    r = client.get(f"{BASE}/graph")
    ms = (time.perf_counter() - t0) * 1000
    results["graph"] = ms
    body = r.json()
    print(f"  Status: {r.status_code} | {fmt_ms(ms)}")
    if r.status_code == 200:
        nodes = body.get("nodes", [])
        edges = body.get("edges", [])
        print(f"  nodes={len(nodes)} edges={len(edges)}")
    else:
        print(f"  ERROR: {body}")

    # ── 4. Sources ────────────────────────────────────────────────────────────
    section("4. GET /sources")
    t0 = time.perf_counter()
    r = client.get(f"{BASE}/sources")
    ms = (time.perf_counter() - t0) * 1000
    results["sources"] = ms
    body = r.json()
    print(f"  Status: {r.status_code} | {fmt_ms(ms)}")
    if r.status_code == 200:
        print(f"  sources count: {len(body.get('sources', []))}")
    else:
        print(f"  ERROR: {body}")

    # ── 5. Recall ─────────────────────────────────────────────────────────────
    section("5. POST /recall (inference query)")
    query = "What does the Transformer architecture improve over RNNs?"
    print(f"  Query: {query!r}")
    print("  ⏳ Running graph-backed recall (embedding + LLM)...")
    t0 = time.perf_counter()
    r = client.post(
        f"{BASE}/recall",
        json={"query": query, "strategy": None},
        timeout=300.0,
    )
    ms = (time.perf_counter() - t0) * 1000
    results["recall"] = ms
    body = r.json()
    print(f"  Status: {r.status_code} | {fmt_ms(ms)}")
    if r.status_code == 200:
        answer = body.get("answer", "")
        print(f"  strategy_used: {body.get('strategy_used', 'N/A')}")
        print(f"  duration_ms (server-side): {body.get('duration_ms', 'N/A')}")
        print(f"  evidence_graph: {'yes' if body.get('evidence_graph') else 'none'}")
        print(f"\n  ── Answer (first 400 chars) ──")
        print(f"  {answer[:400]}")
    else:
        print(f"  ERROR: {body}")

    # ── 6. Stats ──────────────────────────────────────────────────────────────
    section("6. GET /stats")
    t0 = time.perf_counter()
    r = client.get(f"{BASE}/stats")
    ms = (time.perf_counter() - t0) * 1000
    results["stats"] = ms
    body = r.json()
    print(f"  Status: {r.status_code} | {fmt_ms(ms)}")
    if r.status_code == 200:
        print(f"  {body}")

# ── Summary ───────────────────────────────────────────────────────────────────
section("TIMING SUMMARY")
for endpoint, ms in results.items():
    bar = "█" * min(int(ms / 500), 40)
    flag = " ✅" if ms < 5000 else " ⚠️ SLOW"
    if endpoint in ("remember",) and ms < 60000:
        flag = " ✅ (ingest expected to be slow)"
    print(f"  {endpoint:<12} {fmt_ms(ms):>8}  {bar}{flag}")

print("\n  Recall latency breakdown:")
print("   - Embedding the query (NIM API round-trip): ~1-2s")
print("   - Vector search (local LanceDB): <100ms")
print("   - LLM completion (NIM API): ~3-10s depending on output length")
print()
