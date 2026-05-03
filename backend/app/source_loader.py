from __future__ import annotations

from pathlib import Path
import re

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


def load_source_text(source_path: Path) -> str:
    suffix = source_path.suffix.lower()

    if suffix == ".txt":
        return source_path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        return _extract_text_from_pdf(source_path)

    supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    raise ValueError(f"Unsupported input format: {source_path.name}. Supported: {supported}")


def _extract_text_from_pdf(source_path: Path) -> str:
    try:
        reader = PdfReader(str(source_path))
    except Exception as error:  # pragma: no cover, pypdf raises varied error types.
        raise ValueError(f"Failed to read PDF: {source_path.name}") from error

    page_text: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = _normalize_pdf_text(text)
        if text.strip():
            page_text.append(text.strip())

    if not page_text:
        raise ValueError(
            f"No extractable text found in PDF: {source_path.name}. "
            "If this is a scanned PDF, OCR is required before parsing."
        )

    return "\n\n".join(page_text)


def _normalize_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # join words broken by line-wrap hyphenation
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # preserve line boundaries because USPTO PDFs expose headings and numbered paragraphs as separate lines
    # paragraph wrapping is handled by the parser
    text = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text
