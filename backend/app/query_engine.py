from __future__ import annotations

from .models import (
    ContainsFilter,
    CpcFilter,
    Document,
    AndExpression,
    FilterExpression,
    MetadataFilter,
    NotExpression,
    OrExpression,
    Query,
    QueryClause,
    QueryExpression,
    QueryFilter,
    QueryMatch,
    QueryResult,
    Section,
    SectionFilter,
)

METADATA_FIELD_ALIASES = {
    "application_filing_date": "applicationFilingDate",
    "application_no": "applicationNo",
    "document_id": "documentId",
    "filing_date": "filingDate",
    "ingested_at": "ingestedAt",
    "publication_date": "publicationDate",
    "source_file": "sourceFile",
    "us_class_current": "usClassCurrent",
}


class _Candidate:
    def __init__(self, *, passage, section: Section):
        self.passage = passage
        self.section = section
        self.reasons: list[str] = []


def execute_query(document: Document, query: Query) -> QueryResult:
    matches_by_passage_id: dict[str, QueryMatch] = {}
    expression = query.expression

    if expression is None:
        expression = _groups_to_expression(query.groups or [[QueryClause(filter=query_filter) for query_filter in query.filters]])

    for candidate in _flatten(document):
        matched, reasons = _evaluate_expression(document, candidate, expression)
        if matched:
            candidate.reasons.extend(reasons)
            match = _candidate_to_match(document, candidate)
            matches_by_passage_id[match.passageId] = match

    matches = list(matches_by_passage_id.values())

    return QueryResult(totalMatches=len(matches), matches=matches)


def _evaluate_expression(document: Document, candidate: _Candidate, expression: QueryExpression) -> tuple[bool, list[str]]:
    if isinstance(expression, FilterExpression):
        matched = _filter_matches(document, candidate, expression.filter)
        return matched, [_reason(expression.filter, False)] if matched else []

    if isinstance(expression, NotExpression):
        matched, _ = _evaluate_expression(document, candidate, expression.expression)
        if matched:
            return False, []
        return True, [_not_reason(expression.expression)]

    if isinstance(expression, AndExpression):
        reasons: list[str] = []
        for child in expression.expressions:
            matched, child_reasons = _evaluate_expression(document, candidate, child)
            if not matched:
                return False, []
            reasons.extend(child_reasons)
        return True, reasons

    if isinstance(expression, OrExpression):
        reasons: list[str] = []
        matched_any = False
        for child in expression.expressions:
            matched, child_reasons = _evaluate_expression(document, candidate, child)
            if matched:
                matched_any = True
                reasons.extend(reason for reason in child_reasons if reason not in reasons)
        return matched_any, reasons

    return False, []


def _filter_matches(document: Document, candidate: _Candidate, query_filter: QueryFilter) -> bool:
    if isinstance(query_filter, MetadataFilter):
        return _metadata_matches(document, query_filter.field, query_filter.value)

    if isinstance(query_filter, CpcFilter):
        return _cpc_matches(document, query_filter.value)

    if isinstance(query_filter, SectionFilter):
        return candidate.section.type == query_filter.value

    if isinstance(query_filter, ContainsFilter):
        return query_filter.value.lower() in candidate.passage.text.lower()

    return False


def _reason(query_filter: QueryFilter, negated: bool) -> str:
    prefix = "Matched NOT " if negated else "Matched "

    if isinstance(query_filter, MetadataFilter):
        return f'{prefix}meta.{query_filter.field}:"{query_filter.value}"'

    if isinstance(query_filter, CpcFilter):
        return f'{prefix}cpc:"{query_filter.value}"'

    if isinstance(query_filter, SectionFilter):
        return f"{prefix}section:{query_filter.value}"

    if isinstance(query_filter, ContainsFilter):
        return f'{prefix}contains:"{query_filter.value}"'

    return f"{prefix}unknown"


def _not_reason(expression: QueryExpression) -> str:
    if isinstance(expression, FilterExpression):
        return _reason(expression.filter, True)

    return "Matched NOT group"


def _groups_to_expression(groups: list[list[QueryClause]]) -> QueryExpression:
    group_expressions: list[QueryExpression] = []
    for group in groups:
        expressions = []
        for clause in group:
            expression: QueryExpression = FilterExpression(kind="filter", filter=clause.filter)
            expressions.append(NotExpression(kind="not", expression=expression) if clause.negated else expression)
        group_expressions.append(expressions[0] if len(expressions) == 1 else AndExpression(kind="and", expressions=expressions))

    return group_expressions[0] if len(group_expressions) == 1 else OrExpression(kind="or", expressions=group_expressions)


def _candidate_to_match(document: Document, candidate: _Candidate) -> QueryMatch:
    passages = candidate.section.passages
    index = candidate.passage.index

    return QueryMatch(
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


def execute_query_across_documents(documents: list[Document], query: Query) -> QueryResult:
    matches: list[QueryMatch] = []

    for document in documents:
        matches.extend(execute_query(document, query).matches)

    return QueryResult(totalMatches=len(matches), matches=matches)


def _flatten(document: Document) -> list[_Candidate]:
    output: list[_Candidate] = []

    for section in document.sections:
        for passage in section.passages:
            output.append(_Candidate(passage=passage, section=section))

    return output


def _metadata_matches(document: Document, raw_field: str, expected: str) -> bool:
    value = _metadata_value(document, raw_field)
    if value is None:
        return False

    return any(_scalar_matches(item, expected) for item in _flatten_value(value))


def _metadata_value(document: Document, raw_field: str):
    value = document.metadata.model_dump()
    for part in raw_field.split("."):
        field = _metadata_field_name(part)
        if isinstance(value, dict):
            value = _dict_get_case_insensitive(value, field)
            if value is None:
                return None
            continue

        if isinstance(value, list):
            next_values = []
            for item in value:
                if isinstance(item, dict):
                    item_value = _dict_get_case_insensitive(item, field)
                    if item_value is not None:
                        next_values.append(item_value)
            if not next_values:
                return None
            value = next_values
            continue

        return None

    return value


def _metadata_field_name(raw_field: str) -> str:
    normalized = raw_field.strip()
    return METADATA_FIELD_ALIASES.get(normalized.lower(), normalized)


def _dict_get_case_insensitive(data: dict, key: str):
    if key in data:
        return data[key]

    normalized_key = _normalize_key(key)
    for item_key, value in data.items():
        if _normalize_key(str(item_key)) == normalized_key:
            return value

    return None


def _cpc_matches(document: Document, expected: str) -> bool:
    if not document.metadata.cpc:
        return False

    expected_code = _normalize_cpc_code(expected)
    for entry in document.metadata.cpc:
        code = entry.get("code") if isinstance(entry, dict) else None
        if code and _normalize_cpc_code(code) == expected_code:
            return True

    return False


def _flatten_value(value) -> list:
    if isinstance(value, list):
        output = []
        for item in value:
            output.extend(_flatten_value(item))
        return output

    if isinstance(value, dict):
        output = []
        for item in value.values():
            output.extend(_flatten_value(item))
        return output

    return [value]


def _scalar_matches(value, expected: str) -> bool:
    if value is None:
        return False

    actual = _normalize_scalar(str(value))
    target = _normalize_scalar(expected)
    return actual == target


def _normalize_scalar(value: str) -> str:
    return " ".join(value.casefold().split())


def _normalize_key(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def _normalize_cpc_code(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum() or ch == "/")
