from __future__ import annotations

from .models import (
    ContainsFilter,
    Document,
    Query,
    QueryMatch,
    QueryResult,
    Section,
    SectionFilter,
)


class _Candidate:
    def __init__(self, *, passage, section: Section):
        self.passage = passage
        self.section = section
        self.reasons: list[str] = []


def execute_query(document: Document, query: Query) -> QueryResult:
    candidates = _flatten(document)

    for query_filter in query.filters:
        if isinstance(query_filter, SectionFilter):
            filtered: list[_Candidate] = []
            for candidate in candidates:
                if candidate.section.type == query_filter.value:
                    candidate.reasons.append(f"Matched section:{query_filter.value}")
                    filtered.append(candidate)
            candidates = filtered
            continue

        if isinstance(query_filter, ContainsFilter):
            needle = query_filter.value.lower()
            filtered = []
            for candidate in candidates:
                if needle in candidate.passage.text.lower():
                    candidate.reasons.append(f'Matched contains:"{query_filter.value}"')
                    filtered.append(candidate)
            candidates = filtered

    matches: list[QueryMatch] = []

    for candidate in candidates:
        passages = candidate.section.passages
        index = candidate.passage.index

        matches.append(
            QueryMatch(
                passageId=candidate.passage.id,
                documentId=document.metadata.id,
                sectionType=candidate.section.type,
                sectionTitle=candidate.section.title,
                passageIndex=index,
                passageText=candidate.passage.text,
                contextBefore=passages[index - 1].text if index > 0 else None,
                contextAfter=passages[index + 1].text if index < len(passages) - 1 else None,
                reasons=candidate.reasons,
            )
        )

    return QueryResult(totalMatches=len(matches), matches=matches)


def _flatten(document: Document) -> list[_Candidate]:
    output: list[_Candidate] = []

    for section in document.sections:
        for passage in section.passages:
            output.append(_Candidate(passage=passage, section=section))

    return output
