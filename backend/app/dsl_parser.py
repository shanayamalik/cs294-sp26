from __future__ import annotations

import re

from .models import ContainsFilter, Query, SectionFilter, coerce_section_type


def parse_dsl(query_text: str) -> Query:
    trimmed = query_text.strip()
    if not trimmed:
        raise ValueError("Query is empty.")

    clauses = _split_and_clauses(trimmed)
    filters = [_parse_clause(clause) for clause in clauses]

    if not filters:
        raise ValueError("No valid filters found.")

    return Query(filters=filters)


def _split_and_clauses(query_text: str) -> list[str]:
    clauses: list[str] = []
    in_quotes = False
    current: list[str] = []

    i = 0
    while i < len(query_text):
        ch = query_text[i]

        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
            i += 1
            continue

        if not in_quotes and query_text[i : i + 4].upper() == " AND":
            clause = "".join(current).strip()
            if clause:
                clauses.append(clause)
            current = []
            i += 4
            continue

        current.append(ch)
        i += 1

    if in_quotes:
        raise ValueError("Unclosed quote in query.")

    clause = "".join(current).strip()
    if clause:
        clauses.append(clause)

    return clauses


def _parse_clause(clause: str):
    section_match = re.match(r"^section:([A-Za-z_\-\s]+)$", clause, flags=re.IGNORECASE)
    if section_match:
        section_type = coerce_section_type(section_match.group(1))
        if section_type is None:
            raise ValueError(f"Unknown section type: {section_match.group(1)}")
        return SectionFilter(kind="section", value=section_type)

    contains_match = re.match(r'^contains:(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if contains_match:
        phrase = (contains_match.group(1) or contains_match.group(2) or "").strip()
        if not phrase:
            raise ValueError("contains filter requires a non-empty phrase.")
        return ContainsFilter(kind="contains", value=phrase)

    raise ValueError(f"Unsupported clause: {clause}")
