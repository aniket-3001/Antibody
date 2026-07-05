"""MemoryService — the ONE place Cognee is touched (version-churn shield, §M2).

Antibody runs Cognee single-user, single shared dataset ("antibody_global") —
herd immunity is the point (spec §12), so we deliberately DISABLE
ENABLE_BACKEND_ACCESS_CONTROL and skip meetgraph's per-org service users.

The four hackathon verbs map here:
  remember → add() + cognify(graph_model=ScamOntology, temporal_cognify=True)
  recall   → search(GRAPH_COMPLETION, include_references=True)   [cited]
  improve  → memify()   (reinforce recurring tactics, decay stale families §9)
  forget   → forget()   (prune false positives / dead campaigns / poison §10)

Every method degrades gracefully: if Cognee isn't installed or has no LLM key,
MemoryUnavailable is raised and the verdict engine falls back to the
deterministic + semantic layer — Cognee is the star, never a single point of
failure for the demo.

Pinned cognee==1.2.2 (verified locally against tag v1.2.2).
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from api.config import settings

log = logging.getLogger("antibody.memory")


class MemoryUnavailable(RuntimeError):
    """Cognee not installed/configured — callers surface a fallback, never crash."""


def doc_header(channel: str | None, family: str | None, date_iso: str) -> str:
    """Shared-entity convention (meetgraph §5.2 pattern). Consistent tags let
    cognify merge Tactic/Lure/Family nodes across reports."""
    return (
        f"[source: scam_report] [channel: {channel or 'unknown'}] "
        f"[family: {family or 'unknown'}] [date: {date_iso}]"
    )


class MemoryService:
    def __init__(self) -> None:
        self._ready = False

    async def _ensure_ready(self) -> None:
        if self._ready:
            return
        settings.export_cognee_env()
        # Keep every heavy cache off the full C: drive.
        data_root = settings.data_dir.resolve()
        cache_root = data_root / "cache"
        cache_root.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(cache_root / "hf"))
        os.environ.setdefault("FASTEMBED_CACHE_PATH", str(cache_root / "fastembed"))
        # Single shared graph: no access control, no per-user dataset scoping.
        os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

        try:
            import cognee
        except ImportError as exc:  # pragma: no cover
            raise MemoryUnavailable("cognee is not installed") from exc

        # Route Cognee's stores onto D: (its default is fine, but be explicit).
        try:
            cognee.config.system_root_directory(str(data_root / "cognee_system"))
            cognee.config.data_root_directory(str(data_root / "cognee_data"))
        except Exception:  # config surface varies across versions — non-fatal
            log.debug("cognee.config directory setters unavailable", exc_info=True)

        try:
            from cognee.modules.engine.operations.setup import setup

            await setup()
        except Exception:  # fresh embedded DBs self-init on first add in some builds
            log.debug("cognee setup() skipped/failed", exc_info=True)

        self._ready = True

    # ----- remember -----

    async def add(self, data: Any, *, channel: str | None = None,
                  family: str | None = None) -> str | None:
        """Ingest text OR a list of raw files (multimodal, native loaders §11).

        Returns Cognee's own per-document data_id (UUID string) so callers can
        later scope a forget() to exactly this document; None if Cognee's
        result didn't report one (e.g. some file-ingest builds).
        """
        await self._ensure_ready()
        import cognee

        date_iso = datetime.now(UTC).date().isoformat()
        if isinstance(data, str):
            doc = doc_header(channel, family, date_iso) + "\n" + data
            payload: Any = doc
        else:
            # list of raw file paths (image/audio) — let native loaders extract
            payload = data

        node_set = [f"channel:{channel}"] if channel else None
        try:
            if node_set:
                result = await cognee.add(payload, dataset_name=settings.dataset_name, node_set=node_set)
            else:
                result = await cognee.add(payload, dataset_name=settings.dataset_name)
        except TypeError:
            # older/newer signature without node_set kwarg
            result = await cognee.add(payload, dataset_name=settings.dataset_name)
        return _extract_data_id(result)

    async def cognify(self) -> None:
        await self._ensure_ready()
        import cognee

        from api.memory.ontology import build_graph_model

        try:
            await cognee.cognify(
                datasets=[settings.dataset_name],
                graph_model=build_graph_model(),
                temporal_cognify=True,  # powers "emerged N days ago" + evolution (§8)
            )
        except Exception as exc:
            raise MemoryUnavailable(f"cognify failed: {exc}") from exc

    # ----- recall (cited) -----

    async def search(self, query: str, search_type: str = "GRAPH_COMPLETION",
                     top_k: int = 10) -> dict:
        """Cited Q&A → {answer, citations, raw}. Empty (not error) on empty graph."""
        try:
            await self._ensure_ready()
        except MemoryUnavailable:
            return {"answer": "", "citations": [], "raw": [], "available": False}
        import cognee
        from cognee import SearchType

        st = search_type
        if st == "GRAPH_COMPLETION" and _wants_temporal(query):
            st = "TEMPORAL"
        try:
            results = await cognee.search(
                query_text=query,
                query_type=getattr(SearchType, st, SearchType.GRAPH_COMPLETION),
                datasets=[settings.dataset_name],
                top_k=top_k,
                include_references=True,
            )
            shaped = self._shape_results(results)
            shaped["available"] = True
            return shaped
        except Exception as exc:
            log.debug("search failed (type=%s): %s", st, exc)
            # one retry on the plain graph type before giving up
            try:
                results = await cognee.search(
                    query_text=query,
                    query_type=SearchType.GRAPH_COMPLETION,
                    datasets=[settings.dataset_name],
                    top_k=top_k,
                    include_references=True,
                )
                shaped = self._shape_results(results)
                shaped["available"] = True
                return shaped
            except Exception:
                return {"answer": "", "citations": [], "raw": [], "available": False}

    # ----- improve / forget -----

    async def memify(self) -> None:
        await self._ensure_ready()
        import cognee

        if hasattr(cognee, "memify"):
            await cognee.memify()
        elif hasattr(cognee, "improve"):
            await cognee.improve()

    async def forget(self, *, data_id: str | None = None, everything: bool = False) -> dict:
        """Scoped delete (spec §10). Cognee requires data_id to be paired with
        a dataset — always scope to Antibody's single shared dataset so a
        forget() never risks touching another dataset's data."""
        await self._ensure_ready()
        import cognee

        if everything:
            return await cognee.forget(everything=True)
        if not data_id:
            raise ValueError("forget() requires data_id (or everything=True)")
        import uuid

        return await cognee.forget(data_id=uuid.UUID(str(data_id)), dataset=settings.dataset_name)

    # ----- helpers -----

    @staticmethod
    def _shape_results(results: Any) -> dict:
        """Normalize cognee search output → {answer, citations, raw}
        (meetgraph _shape_results, trimmed of meeting-specific enrichment)."""
        answer_parts: list[str] = []
        citations: list[dict] = []
        raw: list[str] = []

        texts: list[str] = []
        for r in results or []:
            if isinstance(r, dict):
                sr = r.get("search_result") or r.get("text") or r.get("answer")
                if isinstance(sr, (list, tuple)):
                    texts.extend(str(x) for x in sr)
                elif sr is not None:
                    texts.append(str(sr))
                else:
                    texts.append(str(r))
            elif isinstance(r, (list, tuple)):
                texts.extend(str(x) for x in r)
            else:
                texts.append(str(r))

        for text in texts:
            raw.append(text)
            if "Evidence:" in text:
                answer, _, evidence = text.partition("Evidence:")
                answer_parts.append(answer.strip())
                citations.extend(_parse_citations(evidence))
            else:
                answer_parts.append(text.strip())

        return {
            "answer": "\n\n".join(p for p in answer_parts if p),
            "citations": citations,
            "raw": raw,
        }


def _extract_data_id(result: Any) -> str | None:
    """Pull the real per-document data_id out of cognee.add()'s pipeline
    result (result.data_ingestion_info[0]["data_id"]) — the id forget()
    needs to scope a deletion to exactly one document."""
    info = getattr(result, "data_ingestion_info", None) or []
    if info and isinstance(info[0], dict) and info[0].get("data_id"):
        return str(info[0]["data_id"])
    return None


def _parse_citations(evidence: str) -> list[dict]:
    """Turn cognee's Evidence block into UI-friendly citation snippets."""
    import re

    out: list[dict] = []
    for item in re.split(r"\n- |\A- ", evidence.strip()):
        item = item.strip().strip("-• ")
        if not item:
            continue
        m = re.match(r'(?s)(chunk \d+) of document (\S+) \(([^)]*)\):\s*"(.*)"?\s*$', item)
        if m:
            snippet = m.group(4).strip().strip('"')
            speech = re.sub(r"^\[source:.*?\]\s*", "", snippet).strip()
            out.append({"snippet": (speech or snippet)[:280], "ref": m.group(1), "doc": m.group(2)})
        else:
            out.append({"snippet": item[:280], "ref": None, "doc": None})
    return out


def _wants_temporal(query: str) -> bool:
    q = f" {query.lower()} "
    hints = (
        "when ", " latest", " recently", " emerging", " emerged", " new campaign",
        " this week", " last week", " timeline", " history", " over time",
        " since ", " first seen", " trending", " climbing",
    )
    return any(h in q for h in hints)


# process-wide singleton
memory_service = MemoryService()
