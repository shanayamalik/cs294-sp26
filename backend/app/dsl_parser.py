from __future__ import annotations

import re
from dataclasses import dataclass

from .models import (
    AndExpression,
    ClaimFilter,
    ContainsFilter,
    CpcFilter,
    FigureFilter,
    FilterExpression,
    HeadingFilter,
    MetadataFilter,
    NotExpression,
    OrExpression,
    ParagraphFilter,
    Query,
    QueryExpression,
    SectionFilter,
    SynonymExpansion,
    coerce_section_type,
)
from .synonym_sets import DATAMUSE_MAX_RESULTS, DATAMUSE_TOPICS, expand_synonym_seed, termset_contains_filters


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
    return Query(expression=expression, synonymExpansions=parser.synonym_expansions)


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
        self.synonym_expansions: list[SynonymExpansion] = []

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
        parsed_clause = _parse_clause(token.value, self.synonym_expansions)
        return parsed_clause if isinstance(parsed_clause, (FilterExpression, AndExpression, OrExpression, NotExpression)) else FilterExpression(kind="filter", filter=parsed_clause)

    def _match(self, kind: str) -> bool:
        if self._current() and self._current().kind == kind:
            self.index += 1
            return True

        return False

    def _current(self) -> _Token | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None


def _parse_clause(clause: str, synonym_expansions: list[SynonymExpansion]):
    if re.match(r"^synonym_of:", clause, flags=re.IGNORECASE):
        seed, max_results, topics = _parse_synonym_of_clause(clause)
        terms = expand_synonym_seed(seed, max_results=max_results, topics=topics)
        synonym_expansions.append(SynonymExpansion(seed=seed, terms=terms, max=max_results, topics=topics))
        contains_expressions = [
            FilterExpression(kind="filter", filter=ContainsFilter(kind="contains", value=term))
            for term in terms
        ]
        return contains_expressions[0] if len(contains_expressions) == 1 else OrExpression(kind="or", expressions=contains_expressions)

    termset_match = re.match(r'^termset:(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if termset_match:
        seed = (termset_match.group(1) or termset_match.group(2) or "").strip()
        if not seed:
            raise ValueError("termset filter requires a non-empty termset name.")

        contains_expressions = [
            FilterExpression(kind="filter", filter=contains_filter)
            for contains_filter in termset_contains_filters(seed)
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

    heading_match = re.match(r'^(?:heading|sectionTitle):(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if heading_match:
        heading = (heading_match.group(1) or heading_match.group(2) or "").strip()
        if not heading:
            raise ValueError("heading filter requires a non-empty value.")
        return HeadingFilter(kind="heading", value=heading)

    cpc_match = re.match(r'^cpc:(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if cpc_match:
        code = (cpc_match.group(1) or cpc_match.group(2) or "").strip()
        if not code:
            raise ValueError("cpc filter requires a non-empty code.")
        return CpcFilter(kind="cpc", value=code)
    paragraph_match = re.match(r'^paragraph:([0-9]+)$', clause, flags=re.IGNORECASE)
    if paragraph_match:
        return ParagraphFilter(kind="paragraph", value=paragraph_match.group(1))

    claim_match = re.match(r'^claim:([0-9]+)$', clause, flags=re.IGNORECASE)
    if claim_match:
        return ClaimFilter(kind="claim", value=int(claim_match.group(1)))

    figure_match = re.match(r'^figure:(?:"([^"]+)"|(.+))$', clause, flags=re.IGNORECASE)
    if figure_match:
        figure_ref = (figure_match.group(1) or figure_match.group(2) or "").strip()
        if not figure_ref:
            raise ValueError("figure filter requires a non-empty reference.")
        return FigureFilter(kind="figure", value=figure_ref)

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


def _parse_synonym_of_clause(clause: str) -> tuple[str, int, str]:
    parts = _split_pipe_options(clause)
    synonym_match = re.match(r'^synonym_of:(?:"([^"]+)"|(.+))$', parts[0], flags=re.IGNORECASE)
    if not synonym_match:
        raise ValueError("synonym_of filter requires a non-empty term.")

    seed = (synonym_match.group(1) or synonym_match.group(2) or "").strip()
    if not seed:
        raise ValueError("synonym_of filter requires a non-empty term.")

    max_results = DATAMUSE_MAX_RESULTS
    topics = DATAMUSE_TOPICS
    seen_options: set[str] = set()

    for option in parts[1:]:
        option_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.+)$", option)
        if not option_match:
            raise ValueError(f"Invalid synonym_of option: {option}")

        key = option_match.group(1).strip().lower()
        value = _unquote_option_value(option_match.group(2).strip())
        if key in seen_options:
            raise ValueError(f"Duplicate synonym_of option: {key}")
        seen_options.add(key)

        if key == "max":
            try:
                max_results = int(value)
            except ValueError as error:
                raise ValueError("synonym_of max option must be a positive integer.") from error
            if max_results < 1:
                raise ValueError("synonym_of max option must be a positive integer.")
            continue

        if key == "topics":
            topics = value.strip()
            if not topics:
                raise ValueError("synonym_of topics option requires a non-empty value.")
            continue

        raise ValueError(f"Unsupported synonym_of option: {key}")

    return seed, max_results, topics


def _split_pipe_options(clause: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False

    for character in clause:
        if character == '"':
            in_quotes = not in_quotes
            current.append(character)
            continue

        if character == "|" and not in_quotes:
            part = "".join(current).strip()
            if not part:
                raise ValueError("Empty synonym_of option.")
            parts.append(part)
            current = []
            continue

        current.append(character)

    part = "".join(current).strip()
    if not part:
        raise ValueError("Empty synonym_of option.")
    parts.append(part)
    return parts


def _unquote_option_value(value: str) -> str:
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1]
    return value
