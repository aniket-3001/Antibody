"""One-off doc ingestion for the Help chatbot's graph.

Usage:
    python -m help_api.ingest ./help_docs
    python -m help_api.ingest ./help_docs/setup.md ./help_docs/faq.pdf

Hands raw .md/.pdf/.txt files straight to Cognee's native loaders (same
"raw file in, let cognee read it" approach api/intake/router.py uses for
uploaded screenshots/PDFs), then cognifies once at the end. Re-run any time
docs change — safe to run repeatedly, cognee dedupes by content.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from help_api.memory_service import help_memory_service

SUPPORTED = {".md", ".pdf", ".txt"}


def _collect(paths: list[str]) -> list[str]:
    files: list[str] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(str(f) for f in sorted(path.rglob("*")) if f.suffix.lower() in SUPPORTED)
        elif path.suffix.lower() in SUPPORTED:
            files.append(str(path))
    return files


async def main(paths: list[str]) -> None:
    files = _collect(paths)
    if not files:
        print(f"No .md/.pdf/.txt files found under {paths}")
        return

    print(f"Ingesting {len(files)} file(s):")
    for f in files:
        print(f"  {f}")

    await help_memory_service.add(files)
    print("Cognifying (this builds/updates the graph — can take a bit)...")
    await help_memory_service.cognify()
    print("Done.")


if __name__ == "__main__":
    args = sys.argv[1:] or ["./help_docs"]
    asyncio.run(main(args))
