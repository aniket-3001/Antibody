# Antibody documentation

Everything about how Antibody works, why it's built the way it is, and how to run,
extend, and deploy it. Start with **Architecture** for the big picture, then dive
into whichever layer you're working on.

| Doc | What's inside |
|---|---|
| [Architecture](architecture.md) | The system at a glance: request lifecycle, the two-store design (Cognee graph + ops DB), fast path vs. background enrichment, and how a report becomes a verdict. |
| [Confidence engine](confidence-engine.md) | The heart of Antibody: five signals, noisy-OR fusion, the four verdict bands, and the **asymmetric safety gate** that guarantees a legit message can never be hard-accused. With worked examples. |
| [Memory layer](memory-layer.md) | How Antibody uses Cognee: the four verbs (`remember` / `recall` / `improve` / `forget`), the shared-node ontology, and graceful degradation when no LLM key is set. |
| [Data model](data-model.md) | The ops SQLite schema, the Cognee graph ontology, and the in-memory semantic index — what lives where and why. |
| [API reference](api-reference.md) | Every endpoint with request/response shapes, the error envelope, and `curl` examples. |
| [Security & privacy](security-and-privacy.md) | PII handling, the de-identified graph, reporter-trust anti-poisoning, the asymmetric gate as a safety property, and indicator/URL safety. |
| [Deployment](deployment.md) | Docker, Google Cloud Run (with the two non-obvious flags that matter), Render, environment variables, and secret handling. |
| [Contributing](contributing.md) | Local setup, the test/lint/type/pre-commit workflow, code style, and how to add a new scam family. |

## The one-paragraph version

A person forwards a suspicious text, screenshot, or scam-call recording. Antibody
extracts hard indicators (URLs, phone numbers, wallets) and soft signals (tactics,
lures), matches them against a **shared Cognee knowledge graph** of known scam
campaigns, and fuses five independent signals into one of four verdict bands —
returning a verdict, a cited explanation, and concrete next steps. Every report,
confirmed or false-positive, makes the graph smarter for the next person. It runs
correctly with **no LLM key** (deterministic + local semantic matching); a key
additionally lights up Cognee's cited graph explanations and the improve/forget
feedback loop.
