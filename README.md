# MemoryOS

A persistent memory operating system for researchers, built on [Cognee](https://www.cognee.ai/)'s hybrid graph-vector memory. Submission for the Cognee Hackathon 2026 (Open Source Track).

MemoryOS is not a chatbot and not a RAG app — it demonstrates what becomes possible when an AI's memory of a research process persists and grows across unlimited sessions, forming a real knowledge graph over papers, methods, hypotheses, and findings.

## Documentation

- [`Docs/PRODUCT_PRD.md`](Docs/PRODUCT_PRD.md) — product vision & scope
- [`Docs/ARCHITECTURE.md`](Docs/ARCHITECTURE.md) — system architecture & data flow
- [`Docs/ONTOLOGY.md`](Docs/ONTOLOGY.md) — the research knowledge graph schema
- [`Docs/MEMORY_CORE_DESIGN.md`](Docs/MEMORY_CORE_DESIGN.md) — `memory_core` module design (public API, provider abstraction, data models)
- [`Docs/MILESTONE_1_REPORT.md`](Docs/MILESTONE_1_REPORT.md) — Milestone 1 validation report
- [`Docs/PROGRESS.md`](Docs/PROGRESS.md) — current status, read first when resuming work
- [`Docs/HACKATHON_CONTEXT.md`](Docs/HACKATHON_CONTEXT.md) — hackathon submission context

## Status

**Milestone 2 complete.** [`memory_core/`](memory_core/) is the real, isolated Cognee integration module — the only part of MemoryOS that imports Cognee directly. It implements the full lifecycle (`ingest`/`improve`/`recall`/`forget`/`find_evidence`/`reset_project`/`get_graph`/`get_stats`/`list_sources`) against Cognee 1.2.2 + Anthropic (Mode A). `tests/reproduce_milestone_1.py` proves it reproduces Milestone 1's validated result end-to-end through the public API alone.

[`prototype/memory_core_spike/`](prototype/memory_core_spike/) — the original Milestone 1 spike — is superseded and kept for historical reference only.

Next: Milestone 3 (Backend API — FastAPI over `memory_core`).
