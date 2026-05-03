from __future__ import annotations

from datetime import datetime, timezone
import re

from .models import Document, DocumentMetadata, Passage, Section, infer_section_type

HEADING_PATTERN = re.compile(r"^[A-Z][A-Z0-9,()/\-\s]{2,}:?$")
PATENT_PARAGRAPH_PATTERN = re.compile(r"(?m)(?=^(?:[A-Z][A-Z0-9 ,()/\-]{2,}\s+)?\(\d+\)\s)")
CLAIM_PATTERN = re.compile(r"(?m)(?=^\d+\.\s)")
FIGURE_REF_PATTERN = re.compile(r"\bFIGS?\.?\s+\d+[A-Z]?(?:-\d+[A-Z]?)?\b", re.IGNORECASE)
TOP_LEVEL_HEADINGS = {
    "ABSTRACT": "ABSTRACT",
    "BACKGROUND/SUMMARY": "Background/Summary",
    "DESCRIPTION": "Description",
    "CLAIMS": "Claims",
}
FRONT_MATTER_MARKERS = {
    "DOCUMENT ID",
    "DATE PUBLISHED",
    "INVENTOR INFORMATION",
    "ASSIGNEE INFORMATION",
    "APPLICATION NO",
    "DATE FILED",
    "CPC CURRENT",
    "DOMESTIC PRIORITY (CONTINUITY DATA)",
    "US CLASS CURRENT:",
    "KWIC HITS",
    "APPLICATION FILING DATE",
    "ABSTRACT",
}


def parse_patent_text(*, doc_id: str, source_file: str, raw_text: str) -> Document:
    lines = _clean_lines(raw_text)
    first_non_empty = next((line for line in lines if line.strip()), "Untitled Document")
    metadata = _extract_metadata(lines)
    title = metadata.pop("title", None) or first_non_empty.strip()

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
            title=title,
            sourceFile=source_file,
            ingestedAt=datetime.now(timezone.utc).isoformat(),
            documentId=metadata.get("documentId"),
            publicationDate=metadata.get("publicationDate"),
            applicationNo=metadata.get("applicationNo"),
            filingDate=metadata.get("filingDate"),
            applicationFilingDate=metadata.get("applicationFilingDate"),
            inventors=metadata.get("inventors"),
            assignee=metadata.get("assignee"),
            cpc=metadata.get("cpc"),
            domesticPriority=metadata.get("domesticPriority"),
            usClassCurrent=metadata.get("usClassCurrent"),
        ),
        sections=sections,
    )


def _clean_lines(raw_text: str) -> list[str]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    return [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.splitlines()]


def _extract_metadata(lines: list[str]) -> dict[str, object]:
    front_matter = _front_matter_lines(lines)
    if not front_matter:
        return {}

    metadata: dict[str, object] = {
        "documentId": _value_after(front_matter, "DOCUMENT ID"),
        "publicationDate": _value_after(front_matter, "DATE PUBLISHED"),
        "applicationNo": _value_after(front_matter, "APPLICATION NO"),
        "filingDate": _value_after(front_matter, "DATE FILED"),
        "applicationFilingDate": _value_after(front_matter, "APPLICATION FILING DATE"),
        "title": _extract_title(front_matter),
        "inventors": _extract_inventors(front_matter),
        "assignee": _extract_assignee(front_matter),
        "cpc": _extract_cpc(front_matter),
        "domesticPriority": _extract_multiline_block(
            front_matter,
            "DOMESTIC PRIORITY (CONTINUITY DATA)",
            {"US CLASS CURRENT:", "KWIC HITS", "APPLICATION FILING DATE"},
        ),
        "usClassCurrent": _extract_us_class(front_matter),
    }
    return {key: value for key, value in metadata.items() if value}


def _front_matter_lines(lines: list[str]) -> list[str]:
    abstract_index = _first_matching_line(lines, "ABSTRACT")
    if abstract_index is None:
        return []
    return [line for line in lines[:abstract_index] if line]


def _first_matching_line(lines: list[str], value: str) -> int | None:
    expected = value.upper()
    for index, line in enumerate(lines):
        if line.strip().upper() == expected:
            return index
    return None


def _value_after(lines: list[str], label: str) -> str | None:
    index = _first_matching_line(lines, label)
    if index is None:
        return None
    for value in lines[index + 1 :]:
        if value:
            return value
    return None


def _extract_title(lines: list[str]) -> str | None:
    cpc_index = _first_matching_line(lines, "CPC CURRENT")
    start_index = cpc_index + 1 if cpc_index is not None else None

    if start_index is not None:
        while start_index < len(lines):
            line = lines[start_index]
            if line.upper() == "TYPE CPC DATE" or line.startswith("CPC"):
                start_index += 1
                continue
            break
    else:
        filed_index = _first_matching_line(lines, "DATE FILED")
        start_index = filed_index + 2 if filed_index is not None else 0

    title_lines: list[str] = []
    for line in lines[start_index:]:
        normalized = line.upper()
        if normalized in FRONT_MATTER_MARKERS:
            break
        if normalized.startswith("US CLASS CURRENT"):
            break
        if line:
            title_lines.append(line)

    return _join_text(title_lines) if title_lines else None


def _extract_inventors(lines: list[str]) -> list[dict[str, str]] | None:
    block = _extract_multiline_block(lines, "INVENTOR INFORMATION", {"ASSIGNEE INFORMATION"})
    if not block:
        return None

    inventors: list[dict[str, str]] = []
    for line in block:
        if line.upper() == "NAME CITY STATE ZIP CODE COUNTRY":
            continue
        inventor: dict[str, str] = {"raw": line}
        right_match = re.match(r"^(?P<prefix>.+?)\s+(?P<zip>N/A|[\d-]+)\s+(?P<country>[A-Z]{2})$", line)
        if right_match:
            prefix = right_match.group("prefix").strip()
            state_match = re.match(r"^(?P<name_city>.+?)(?:\s+|)(?P<state>N/A|[A-Z]{2})$", prefix)
            if state_match:
                inventor["state"] = state_match.group("state")
                inventor["nameAndCity"] = state_match.group("name_city").strip()
            inventor["zipCode"] = right_match.group("zip")
            inventor["country"] = right_match.group("country")
        inventors.append(inventor)

    return inventors or None


def _extract_assignee(lines: list[str]) -> dict[str, str] | None:
    block = _extract_multiline_block(lines, "ASSIGNEE INFORMATION", {"APPLICATION NO"})
    if not block:
        return None

    labels = {"NAME", "CITY", "STATE", "ZIP CODE", "COUNTRY", "TYPE CODE"}
    result: dict[str, str] = {}
    current_label: str | None = None
    values: list[str] = []

    def flush() -> None:
        nonlocal values
        if current_label and values:
            key = current_label.lower().replace(" ", "")
            result[key] = _join_text(values)
        values = []

    for line in block:
        normalized = line.upper()
        if normalized in labels:
            flush()
            current_label = normalized
        elif current_label:
            values.append(line)
    flush()

    return result or None


def _extract_cpc(lines: list[str]) -> list[dict[str, str]] | None:
    cpc_index = _first_matching_line(lines, "CPC CURRENT")
    if cpc_index is None:
        return None

    entries: list[dict[str, str]] = []
    for line in lines[cpc_index + 1 :]:
        if line.upper() == "TYPE CPC DATE":
            continue
        if not line.startswith("CPC"):
            break
        match = re.match(r"^(?P<type>\S+)\s+(?P<code>.+?)\s+(?P<date>\d{4}-\d{2}-\d{2})$", line)
        if match:
            entries.append(match.groupdict())
        else:
            entries.append({"raw": line})

    return entries or None


def _extract_us_class(lines: list[str]) -> str | None:
    index = _first_matching_line(lines, "US CLASS CURRENT:")
    if index is None:
        return None
    values: list[str] = []
    for line in lines[index + 1 :]:
        if line.upper() in {"KWIC HITS", "APPLICATION FILING DATE"}:
            break
        if line:
            values.append(line)
    return _join_text(values) if values else None


def _extract_multiline_block(lines: list[str], start_label: str, end_labels: set[str]) -> list[str] | None:
    start_index = _first_matching_line(lines, start_label)
    if start_index is None:
        return None

    values: list[str] = []
    for line in lines[start_index + 1 :]:
        normalized = line.upper()
        if normalized in end_labels:
            break
        if line:
            values.append(line)

    return values or None


def _extract_sections(lines: list[str]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    first_section_index = _find_first_section_index(lines)
    scan_lines = lines[first_section_index:] if first_section_index is not None else lines

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

    for line in scan_lines:
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


def _find_first_section_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.strip().upper() in TOP_LEVEL_HEADINGS:
            return index
    return None


def _is_section_heading(line: str) -> bool:
    if not line:
        return False
    normalized = line.upper()
    if normalized in TOP_LEVEL_HEADINGS:
        return True
    if normalized in FRONT_MATTER_MARKERS:
        return False
    if len(line) > 96:
        return False
    return bool(HEADING_PATTERN.match(line))


def _split_into_passages(section_text: str, section_type: str, section_index: int) -> list[Passage]:
    raw_segments = _raw_passage_segments(section_text, section_type)

    passages: list[Passage] = []
    cursor = 0

    for passage_index, raw_segment in enumerate(raw_segments):
        paragraph = _normalize_passage_text(raw_segment)
        if not paragraph:
            continue

        start = section_text.find(raw_segment, cursor)
        safe_start = start if start >= 0 else cursor
        end = safe_start + len(raw_segment)
        figure_refs = _figure_refs(paragraph)

        passages.append(
            Passage(
                id=f"{section_type}-{section_index}-{passage_index}",
                text=paragraph,
                index=passage_index,
                sectionType=section_type,
                startOffset=safe_start,
                endOffset=end,
                paragraphId=_paragraph_id(paragraph) if section_type != "CLAIMS" else None,
                claimNo=_claim_no(paragraph) if section_type == "CLAIMS" else None,
                figureRefs=figure_refs if figure_refs else None,
            )
        )

        cursor = end

    return passages


def _raw_passage_segments(section_text: str, section_type: str) -> list[str]:
    stripped = section_text.strip()
    if not stripped:
        return []

    if section_type == "ABSTRACT":
        return [stripped]

    if section_type == "CLAIMS":
        claim_segments = _split_by_pattern(stripped, CLAIM_PATTERN)
        if len(claim_segments) > 1 or _claim_no(_normalize_passage_text(claim_segments[0])):
            return claim_segments

    paragraph_segments = _split_by_pattern(stripped, PATENT_PARAGRAPH_PATTERN)
    if paragraph_segments and (
        len(paragraph_segments) > 1 or _paragraph_id(_normalize_passage_text(paragraph_segments[0]))
    ):
        return paragraph_segments

    return [segment.strip() for segment in re.split(r"\n\s*\n+", stripped) if segment.strip()]


def _split_by_pattern(text: str, pattern: re.Pattern[str]) -> list[str]:
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    segments: list[str] = []
    if matches[0].start() > 0 and text[: matches[0].start()].strip():
        segments.append(text[: matches[0].start()].strip())

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segment = text[start:end].strip()
        if segment:
            segments.append(segment)

    return segments


def _normalize_passage_text(text: str) -> str:
    return _join_text(line.strip() for line in text.splitlines() if line.strip())


def _join_text(parts) -> str:
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _paragraph_id(text: str) -> str | None:
    match = re.match(r"^(?:[A-Z][A-Z0-9 ,()/\-]{2,}\s+)?\((\d+)\)\s", text)
    return match.group(1) if match else None


def _claim_no(text: str) -> int | None:
    match = re.match(r"^(\d+)\.\s", text)
    return int(match.group(1)) if match else None


def _figure_refs(text: str) -> list[str]:
    refs: list[str] = []
    for match in FIGURE_REF_PATTERN.finditer(text):
        ref = re.sub(r"\s+", " ", match.group(0).upper().replace("FIG ", "FIG. "))
        if ref not in refs:
            refs.append(ref)
    return refs
