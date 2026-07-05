"""HelpMemoryService — Cognee graph over Antibody's own documentation (.md/PDF),
entirely separate from api/memory/memory_service.py's scam-report graph (own
process, own dataset, own storage directory, own LLM/embedding config)."""
from __future__ import annotations

import logging
from typing import Any

from help_api.config import help_settings

log = logging.getLogger("antibody.help.memory")


class MemoryUnavailable(RuntimeError):
    """Cognee not installed/configured for the help service."""


class HelpMemoryService:
    def __init__(self) -> None:
        self._ready = False

    async def _ensure_ready(self) -> None:
        if self._ready:
            return
        help_settings.export_cognee_env()

        import os

        data_root = help_settings.help_data_dir.resolve()
        cache_root = data_root / "cache"
        cache_root.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(cache_root / "hf"))
        os.environ.setdefault("FASTEMBED_CACHE_PATH", str(cache_root / "fastembed"))
        os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

        try:
            import cognee
        except ImportError as exc:  # pragma: no cover
            raise MemoryUnavailable("cognee not installed") from exc

        try:
            cognee.config.system_root_directory(str(data_root / "cognee_system"))
            cognee.config.data_root_directory(str(data_root / "cognee_data"))
        except Exception:
            log.debug("cognee.config directory setters unavailable", exc_info=True)

        try:
            from cognee.modules.engine.operations.setup import setup

            await setup()
        except Exception:
            log.debug("cognee setup() skipped/failed", exc_info=True)

        self._ready = True

    async def add(self, paths: list[str]) -> None:
        """Hand raw doc files (.md/.pdf/...) to Cognee's native loaders."""
        await self._ensure_ready()
        import cognee

        await cognee.add(paths, dataset_name=help_settings.help_dataset_name)

    async def cognify(self) -> None:
        await self._ensure_ready()
        import cognee

        try:
            await cognee.cognify(datasets=[help_settings.help_dataset_name])
        except Exception as exc:
            raise MemoryUnavailable(f"cognify failed: {exc}") from exc

    async def ask(self, query: str, top_k: int = 8) -> dict:
        """Cited Q&A over the docs graph → {answer, citations, available}."""
        try:
            await self._ensure_ready()
        except MemoryUnavailable:
            return {"answer": "", "citations": [], "available": False}

        import asyncio

        import cognee
        from cognee import SearchType

        try:
            # NIM's completions endpoint has been observed to hang (no error,
            # no response) rather than fail fast on some prompts — bound it
            # so a bad prompt degrades to a fallback instead of freezing the
            # chat UI forever.
            results = await asyncio.wait_for(
                cognee.search(
                    query_text=query,
                    query_type=SearchType.GRAPH_COMPLETION,
                    datasets=[help_settings.help_dataset_name],
                    top_k=top_k,
                    include_references=True,
                ),
                timeout=45.0,
            )
            shaped = self._shape_results(results)
            shaped["available"] = True
            return shaped
        except (Exception, TimeoutError) as exc:
            log.debug("help search failed: %s", exc)
            return {"answer": "", "citations": [], "available": False}

    @staticmethod
    def _shape_results(results: Any) -> dict:
        texts: list[str] = []
        for r in results or []:
            if isinstance(r, dict):
                text = r.get("search_result") or r.get("text") or r.get("answer")
                if isinstance(text, list):
                    texts.extend(str(x) for x in text)
                elif text:
                    texts.append(str(text))
                else:
                    texts.append(str(r))
            else:
                texts.append(str(r))

        raw = [t for t in texts if t]
        if not raw:
            return {"answer": "", "citations": []}

        text = raw[0]
        answer, _, evidence = text.partition("Evidence:")
        citations = _parse_citations(evidence) if evidence else []
        return {"answer": answer.strip(), "citations": citations, "raw": raw}


def _parse_citations(evidence: str) -> list[dict]:
    import re

    out: list[dict] = []
    for item in re.split(r"\n- |\A- ", evidence.strip()):
        item = item.strip().strip("-• ")
        if not item:
            continue
        m = re.match(r'(?s)(chunk \d+) of document (\S+) \(([^)]*)\):\s*"?(.*)"?\s*$', item)
        if m:
            snippet = m.group(4).strip().strip('"')
            out.append({"snippet": snippet[:280], "ref": m.group(1), "doc": m.group(2)})
        else:
            out.append({"snippet": item[:280], "ref": None, "doc": None})
    return out


help_memory_service = HelpMemoryService()
