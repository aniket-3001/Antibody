"""PDF adapter — extracts plain text from PDF bytes using PyMuPDF.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3, §9.
Library: PyMuPDF (fitz) — chosen in ARCHITECTURE.md §9 for its speed,
accuracy, and permissive BSD-3 licence when used in server-side pipelines.

Text extraction strategy:
  - Iterate pages in document order.
  - Use get_text("text") for clean plain-text extraction (strips images,
    keeps paragraph structure via newlines).
  - Strip leading/trailing whitespace per page; join pages with double
    newline to preserve section boundaries for the LLM chunker.
  - Raises ValueError for empty or non-extractable PDFs so the caller
    can surface a user-friendly error.
"""

from __future__ import annotations

from typing import Any

from memory_core.models import SourceInput


def load(source: SourceInput) -> tuple[str, dict[str, Any]]:
    """Extract text from a PDF source.

    Args:
        source: SourceInput whose `content` is either raw PDF bytes (bytes)
                or a file-system path string ending in '.pdf'.

    Returns:
        A (text, metadata) tuple where `text` is the full extracted plain
        text and `metadata` is a dict with page_count and source_type.

    Raises:
        ImportError: if PyMuPDF (fitz) is not installed.
        ValueError: if the PDF contains no extractable text.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError(
            "PDF ingestion requires PyMuPDF: pip install pymupdf"
        ) from exc

    content = source.content

    # Accept raw bytes (from multipart upload) or a file path string.
    if isinstance(content, bytes):
        doc = fitz.open(stream=content, filetype="pdf")
    elif isinstance(content, str):
        doc = fitz.open(content)
    else:
        raise ValueError(f"Unsupported content type for PDF adapter: {type(content)!r}")

    pages: list[str] = []
    for page in doc:
        page_text = page.get_text("text").strip()
        if page_text:
            pages.append(page_text)
    doc.close()

    if not pages:
        raise ValueError(
            "PDF contains no extractable text (may be scanned image-only PDF)."
        )

    full_text = "\n\n".join(pages)
    metadata: dict[str, Any] = {
        "source_type": "pdf",
        "page_count": len(pages),
        "title": source.title or "",
    }
    return full_text, metadata
