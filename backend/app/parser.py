from __future__ import annotations

from datetime import datetime, timezone
import re

from .models import Document, DocumentMetadata, Passage, Section, infer_section_type

HEADING_PATTERN = re.compile(r"^[A-Z][A-Z0-9\-\s]{2,}$")


def parse_patent_text(*, doc_id: str, source_file: str, raw_text: str) -> Document:
    lines = raw_text.splitlines()
    first_non_empty = next((line for line in lines if line.strip()), "Untitled Document")

    extracted_sections = _extract_sections(lines)
    sections: list[Section] = []

    for section_index, item in enumerate(extracted_sections):
        passages = _split_into_passages(item["body"], item["type"], section_index)
        sections.append(
            Section(
                type=item["type"],
                title=item["title"],
                passages=passages,
            )
        )

    return Document(
        metadata=DocumentMetadata(
            id=doc_id,
            title=first_non_empty.strip(),
            sourceFile=source_file,
            ingestedAt=datetime.now(timezone.utc).isoformat(),
        ),
        sections=sections,
    )


def _extract_sections(lines: list[str]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []

    current_title = "Preamble"
    current_type = "OTHER"
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        body = "\n".join(buffer).strip()
        if not body:
            buffer = []
            return

        sections.append({"type": current_type, "title": current_title, "body": body})
        buffer = []

    for line in lines:
        normalized = line.strip()

        if _is_section_heading(normalized):
            flush()
            current_title = normalized
            current_type = infer_section_type(normalized)
            continue

        buffer.append(line)

    flush()

    if sections:
        return sections

    return [{"type": "OTHER", "title": "FULL_TEXT", "body": "\n".join(lines).strip()}]


def _is_section_heading(line: str) -> bool:
    if not line:
        return False
    if len(line) > 64:
        return False
    return bool(HEADING_PATTERN.match(line))


def _split_into_passages(section_text: str, section_type: str, section_index: int) -> list[Passage]:
    paragraph_texts = [p.strip() for p in re.split(r"\n\s*\n+", section_text) if p.strip()]

    passages: list[Passage] = []
    cursor = 0

    for passage_index, paragraph in enumerate(paragraph_texts):
        start = section_text.find(paragraph, cursor)
        safe_start = start if start >= 0 else cursor
        end = safe_start + len(paragraph)

        passages.append(
            Passage(
                id=f"{section_type}-{section_index}-{passage_index}",
                text=paragraph,
                index=passage_index,
                sectionType=section_type,
                startOffset=safe_start,
                endOffset=end,
            )
        )

        cursor = end

    return passages
