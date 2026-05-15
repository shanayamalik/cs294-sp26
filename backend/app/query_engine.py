from __future__ import annotations

import re
from datetime import date, datetime
from functools import lru_cache

from .models import (
    ContainsFilter,
    CpcFilter,
    Document,
    AndExpression,
    ClaimFilter,
    FilterExpression,
    FigureFilter,
    MetadataFilter,
    NotExpression,
    OrExpression,
    ParagraphFilter,
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
    "appfiled": "applicationFilingDate",
    "appfileddate": "applicationFilingDate",
    "appno": "applicationNo",
    "appdate": "applicationFilingDate",
    "application_filed": "applicationFilingDate",
    "application_filing_date": "applicationFilingDate",
    "application_no": "applicationNo",
    "application_number": "applicationNo",
    "applicationdate": "applicationFilingDate",
    "admissibility": "admissibilityDate",
    "admissibility_date": "admissibilityDate",
    "admissibilitydate": "admissibilityDate",
    "assignee_name": "assignee.name",
    "assigneename": "assignee.name",
    "document_id": "documentId",
    "docid": "documentId",
    "effective": "effectiveDate",
    "effective_date": "effectiveDate",
    "effectivedate": "effectiveDate",
    "filing": "filingDate",
    "filed": "filingDate",
    "fileddate": "filingDate",
    "filing_date": "filingDate",
    "filingdate": "filingDate",
    "ingested_at": "ingestedAt",
    "inventor_name": "inventors.nameAndCity",
    "inventorname": "inventors.nameAndCity",
    "publication": "publicationDate",
    "pubdate": "publicationDate",
    "pub_date": "publicationDate",
    "published": "publicationDate",
    "publisheddate": "publicationDate",
    "publication_date": "publicationDate",
    "publicationdate": "publicationDate",
    "priority": "priorityDate",
    "priority_date": "priorityDate",
    "prioritydate": "priorityDate",
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
        return _metadata_matches(document, query_filter.field, query_filter.operator, query_filter.value)

    if isinstance(query_filter, CpcFilter):
        return _cpc_matches(document, query_filter.value)

    if isinstance(query_filter, SectionFilter):
        return _section_matches(candidate.section.type, query_filter.value)

    if isinstance(query_filter, ContainsFilter):
        return _contains_matches(candidate.passage.text, query_filter.value, query_filter.mode)

    if isinstance(query_filter, ParagraphFilter):
        return candidate.passage.paragraphId == query_filter.value

    if isinstance(query_filter, ClaimFilter):
        return candidate.passage.claimNo == query_filter.value

    if isinstance(query_filter, FigureFilter):
        return _figure_matches(candidate.passage.figureRefs, query_filter.value)

    return False


def _section_matches(actual: str, expected: str) -> bool:
    if actual == expected:
        return True

    if expected == "SPECIFICATION":
        return actual in {"BACKGROUND", "SUMMARY", "DESCRIPTION", "SPECIFICATION"}

    return False


def _reason(query_filter: QueryFilter, negated: bool) -> str:
    prefix = "Matched NOT " if negated else "Matched "

    if isinstance(query_filter, MetadataFilter):
        operator = {
            "eq": "",
            "lt": "<",
            "lte": "<=",
            "gt": ">",
            "gte": ">=",
            "contains": "~",
            "startswith": "^",
        }[query_filter.operator]
        return f'{prefix}meta.{query_filter.field}:{operator}"{query_filter.value}"'

    if isinstance(query_filter, CpcFilter):
        return f'{prefix}cpc:"{query_filter.value}"'

    if isinstance(query_filter, SectionFilter):
        return f"{prefix}section:{query_filter.value}"

    if isinstance(query_filter, ContainsFilter):
        filter_name = "contains.regex" if query_filter.mode == "regex" else "contains"
        return f'{prefix}{filter_name}:"{query_filter.value}"'

    if isinstance(query_filter, ParagraphFilter):
        return f"{prefix}paragraph:{query_filter.value}"

    if isinstance(query_filter, ClaimFilter):
        return f"{prefix}claim:{query_filter.value}"

    if isinstance(query_filter, FigureFilter):
        return f'{prefix}figure:"{query_filter.value}"'

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
        paragraphId=candidate.passage.paragraphId,
        claimNo=candidate.passage.claimNo,
        figureRefs=candidate.passage.figureRefs,
    )


def execute_query_across_documents(documents: list[Document], query: Query) -> QueryResult:
    matches: list[QueryMatch] = []

    for document in documents:
        matches.extend(execute_query(document, query).matches)

    return QueryResult(totalMatches=len(matches), matches=matches)


def _contains_matches(text: str, expected: str, mode: str = "literal") -> bool:
    if mode == "regex":
        pattern = _compile_contains_pattern(expected)
        return pattern is not None and pattern.search(text) is not None

    return expected.casefold() in text.casefold()


def _figure_matches(actual_refs: list[str] | None, expected: str) -> bool:
    if not actual_refs:
        return False

    normalized_expected = _normalize_figure_ref(expected)
    return any(_normalize_figure_ref(actual_ref) == normalized_expected for actual_ref in actual_refs)


def _normalize_figure_ref(value: str) -> str:
    normalized = re.sub(r"\bFIGURE\b", "FIG", value.upper())
    normalized = normalized.replace(".", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if re.fullmatch(r"[0-9]+[A-Z]?", normalized):
        return f"FIG {normalized}"

    if normalized.startswith("FIG "):
        return normalized

    return normalized


@lru_cache(maxsize=512)
def _compile_contains_pattern(pattern: str):
    try:
        return re.compile(pattern, flags=re.IGNORECASE)
    except re.error:
        return None


def _flatten(document: Document) -> list[_Candidate]:
    output: list[_Candidate] = []

    for section in document.sections:
        for passage in section.passages:
            output.append(_Candidate(passage=passage, section=section))

    return output


def _metadata_matches(document: Document, raw_field: str, operator: str, expected: str) -> bool:
    value = _metadata_value(document, raw_field)
    if value is None:
        return False

    return any(_scalar_matches(item, operator, expected) for item in _flatten_value(value))


def _metadata_value(document: Document, raw_field: str):
    value = document.metadata.model_dump()
    resolved_field = _resolve_metadata_field_path(raw_field)

    derived_value = _derived_metadata_value(document, resolved_field)
    if derived_value is not None:
        return derived_value

    for part in resolved_field.split("."):
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


def _derived_metadata_value(document: Document, resolved_field: str):
    if resolved_field == "priorityDate":
        return _derived_priority_date(document)

    if resolved_field in {"effectiveDate", "admissibilityDate"}:
        return _derived_effective_date(document)

    return None


def _derived_priority_date(document: Document) -> str | None:
    priorities = document.metadata.domesticPriority or []
    priority_dates: list[date] = []

    for entry in priorities:
        if not isinstance(entry, str):
            continue

        for match in re.findall(r"\b\d{8}\b", entry):
            parsed = _parse_date(match)
            if parsed is not None:
                priority_dates.append(parsed)

    if not priority_dates:
        return None

    return min(priority_dates).isoformat()


def _derived_effective_date(document: Document) -> str | None:
    for candidate in (
        _derived_priority_date(document),
        _normalize_date_text(document.metadata.applicationFilingDate),
        _normalize_date_text(document.metadata.filingDate),
    ):
        if candidate is not None:
            return candidate

    return None


def _normalize_date_text(value: str | None) -> str | None:
    if value is None:
        return None

    parsed = _parse_date(value)
    return parsed.isoformat() if parsed is not None else None


def _resolve_metadata_field_path(raw_field: str) -> str:
    normalized = raw_field.strip()
    return METADATA_FIELD_ALIASES.get(normalized.lower(), normalized)


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


def _scalar_matches(value, operator: str, expected: str) -> bool:
    if value is None:
        return False

    actual_text = str(value)
    if operator == "contains":
        return _normalize_scalar(expected) in _normalize_scalar(actual_text)

    if operator == "startswith":
        return _normalize_scalar(actual_text).startswith(_normalize_scalar(expected))

    if operator == "eq":
        actual = _normalize_scalar(actual_text)
        target = _normalize_scalar(expected)
        return actual == target

    actual_comparable = _coerce_comparable(actual_text)
    expected_comparable = _coerce_comparable(expected)
    if actual_comparable is None or expected_comparable is None:
        return False

    if operator == "lt":
        return actual_comparable < expected_comparable
    if operator == "lte":
        return actual_comparable <= expected_comparable
    if operator == "gt":
        return actual_comparable > expected_comparable
    if operator == "gte":
        return actual_comparable >= expected_comparable

    return False


def _coerce_comparable(value: str):
    normalized = value.strip()
    if not normalized:
        return None

    parsed_date = _parse_date(normalized)
    if parsed_date is not None:
        return parsed_date

    if re.fullmatch(r"-?\d+(?:\.\d+)?", normalized):
        return float(normalized)

    return None


def _parse_date(value: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _normalize_scalar(value: str) -> str:
    return " ".join(value.casefold().split())


def _normalize_key(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def _normalize_cpc_code(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum() or ch == "/")
