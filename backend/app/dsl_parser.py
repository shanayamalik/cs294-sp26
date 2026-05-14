from __future__ import annotations

import re
from dataclasses import dataclass

from .models import (
    AndExpression,
    ContainsFilter,
    CpcFilter,
    FilterExpression,
    MetadataFilter,
    NotExpression,
    OrExpression,
    ParagraphFilter,
    Query,
    QueryExpression,
    SectionFilter,
    coerce_section_type,
)
from .synonym_sets import synonym_contains_filters


@dataclass
class _Token:
    kind: str
    value: str


def parse_dsl(query_text: str) -> Query:
    trimmed = query_text.strip()
    if not trimmed:
        raise ValueError("Query is empty.")

    tokens = _tokenize(trimmed)
    parser = _ExpressionParser(tokens)
    expression = parser.parse()
    return Query(expression=expression)


def _operator_at(query_text: str, index: int, operator: str) -> bool:
    end = index + len(operator)
    if query_text[index:end].upper() != operator:
        return False

    before = query_text[index - 1] if index > 0 else " "
    after = query_text[end] if end < len(query_text) else " "
    return before.isspace() and after.isspace()


def _tokenize(query_text: str) -> list[_Token]:
    tokens: list[_Token] = []
    current: list[str] = []
    in_quotes = False
    i = 0

    def flush_clause() -> None:
        clause = "".join(current).strip()
        current.clear()
        if clause:
            tokens.append(_Token("CLAUSE", clause))

    while i < len(query_text):
        ch = query_text[i]

        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
            i += 1
            continue

        if not in_quotes and ch == "(":
            flush_clause()
            tokens.append(_Token("LPAREN", ch))
            i += 1
            continue

        if not in_quotes and ch == ")":
            flush_clause()
            tokens.append(_Token("RPAREN", ch))
            i += 1
            continue

        if not in_quotes:
            matched_operator = next(
                (operator for operator in ("AND", "OR", "NOT") if _operator_at(query_text, i, operator)),
                None,
            )
            if matched_operator:
                flush_clause()
                tokens.append(_Token(matched_operator, matched_operator))
                i += len(matched_operator)
                continue

        current.append(ch)
        i += 1

    if in_quotes:
        raise ValueError("Unclosed quote in query.")

    flush_clause()
    if not tokens:
        raise ValueError("No valid filters found.")

    return tokens


class _ExpressionParser:
    def __init__(self, tokens: list[_Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def parse(self) -> QueryExpression:
        expression = self._parse_or()
        if self._current() is not None:
            raise ValueError(f"Unexpected token: {self._current().value}")
        return expression

    def _parse_or(self) -> QueryExpression:
        expressions = [self._parse_and()]

        while self._match("OR"):
            expressions.append(self._parse_and())

        return expressions[0] if len(expressions) == 1 else OrExpression(kind="or", expressions=expressions)

    def _parse_and(self) -> QueryExpression:
        expressions = [self._parse_not()]

        while self._match("AND"):
            expressions.append(self._parse_not())

        return expressions[0] if len(expressions) == 1 else AndExpression(kind="and", expressions=expressions)

    def _parse_not(self) -> QueryExpression:
        if self._match("NOT"):
            return NotExpression(kind="not", expression=self._parse_not())

        return self._parse_primary()

    def _parse_primary(self) -> QueryExpression:
        if self._match("LPAREN"):
            expression = self._parse_or()
            if not self._match("RPAREN"):
                raise ValueError("Unclosed parenthesis in query.")
            return expression

        token = self._current()
        if token is None:
            raise ValueError("Missing clause.")

        if token.kind != "CLAUSE":
            raise ValueError(f"Expected query clause, got {token.value}.")

        self.index += 1
        parsed_clause = _parse_clause(token.value)
        return parsed_clause if isinstance(parsed_clause, (FilterExpression, AndExpression, OrExpression, NotExpression)) else FilterExpression(kind="filter", filter=parsed_clause)

    def _match(self, kind: str) -> bool:
        if self._current() and self._current().kind == kind:
            self.index += 1
            return True

        return False

    def _current(self) -> _Token | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None


def _parse_clause(clause: str):
    synonym_match = re.match(r'^synonym_of:(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if synonym_match:
        seed = (synonym_match.group(1) or synonym_match.group(2) or "").strip()
        if not seed:
            raise ValueError("synonym_of filter requires a non-empty term.")

        contains_expressions = [
            FilterExpression(kind="filter", filter=contains_filter)
            for contains_filter in synonym_contains_filters(seed)
        ]
        return contains_expressions[0] if len(contains_expressions) == 1 else OrExpression(kind="or", expressions=contains_expressions)

    section_match = re.match(r"^section:([A-Za-z_\-\s]+)$", clause, flags=re.IGNORECASE)
    if section_match:
        section_type = coerce_section_type(section_match.group(1))
        if section_type is None:
            raise ValueError(f"Unknown section type: {section_match.group(1)}")
        return SectionFilter(kind="section", value=section_type)

    contains_match = re.match(r'^contains(?:\.(regex))?:(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if contains_match:
        phrase = (contains_match.group(2) or contains_match.group(3) or "").strip()
        if not phrase:
            raise ValueError("contains filter requires a non-empty phrase.")
        return ContainsFilter(kind="contains", value=phrase, mode="regex" if contains_match.group(1) else "literal")

    cpc_match = re.match(r'^cpc:(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if cpc_match:
        code = (cpc_match.group(1) or cpc_match.group(2) or "").strip()
        if not code:
            raise ValueError("cpc filter requires a non-empty code.")
        return CpcFilter(kind="cpc", value=code)
    paragraph_match = re.match(r'^paragraph:([0-9]+)$', clause, flags=re.IGNORECASE)
    if paragraph_match:
        return ParagraphFilter(kind="paragraph", value=paragraph_match.group(1))
    metadata_match = re.match(r'^meta(?:data)?\.([A-Za-z][A-Za-z0-9_.-]*):(.*)$', clause, flags=re.IGNORECASE)
    if metadata_match:
        field = metadata_match.group(1).strip()
        raw_value = metadata_match.group(2).strip()
        operator = "eq"

        for prefix, operator_name in (("<=", "lte"), (">=", "gte"), ("~", "contains"), ("^", "startswith"), ("<", "lt"), (">", "gt"), ("=", "eq")):
            if raw_value.startswith(prefix):
                operator = operator_name
                raw_value = raw_value[len(prefix) :].strip()
                break

        if raw_value.startswith('"') and raw_value.endswith('"') and len(raw_value) >= 2:
            value = raw_value[1:-1]
        else:
            value = raw_value

        if not value:
            raise ValueError("metadata filter requires a non-empty value.")
        return MetadataFilter(kind="metadata", field=field, operator=operator, value=value)

    raise ValueError(f"Unsupported clause: {clause}")
