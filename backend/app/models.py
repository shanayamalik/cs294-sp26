from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

SectionType = Literal["TITLE", "ABSTRACT", "SPECIFICATION", "CLAIMS", "OTHER"]

SECTION_SYNONYMS: dict[str, SectionType] = {
    "TITLE": "TITLE",
    "ABSTRACT": "ABSTRACT",
    "CLAIM": "CLAIMS",
    "CLAIMS": "CLAIMS",
    "SPECIFICATION": "SPECIFICATION",
    "DESCRIPTION": "SPECIFICATION",
    "DETAILED DESCRIPTION": "SPECIFICATION",
    "BRIEF DESCRIPTION": "SPECIFICATION",
    "BACKGROUND": "SPECIFICATION",
    "SUMMARY": "SPECIFICATION",
    "FIELD": "SPECIFICATION",
    "OTHER": "OTHER",
}


class Passage(BaseModel):
    id: str
    text: str
    index: int
    sectionType: SectionType
    startOffset: int
    endOffset: int
    paragraphId: str | None = None
    claimNo: int | None = None
    figureRefs: list[str] | None = None


class Section(BaseModel):
    type: SectionType
    title: str
    passages: list[Passage]


class DocumentMetadata(BaseModel):
    id: str
    title: str
    sourceFile: str
    ingestedAt: str
    documentId: str | None = None
    publicationDate: str | None = None
    applicationNo: str | None = None
    filingDate: str | None = None
    applicationFilingDate: str | None = None
    inventors: list[dict[str, str]] | None = None
    assignee: dict[str, str] | None = None
    cpc: list[dict[str, str]] | None = None
    domesticPriority: list[str] | None = None
    usClassCurrent: str | None = None


class Document(BaseModel):
    metadata: DocumentMetadata
    sections: list[Section]


class SectionFilter(BaseModel):
    kind: Literal["section"]
    value: SectionType


class ContainsFilter(BaseModel):
    kind: Literal["contains"]
    value: str
    mode: Literal["literal", "regex"] = "literal"


class MetadataFilter(BaseModel):
    kind: Literal["metadata"]
    field: str
    operator: Literal["eq", "lt", "lte", "gt", "gte", "contains", "startswith"] = "eq"
    value: str


class CpcFilter(BaseModel):
    kind: Literal["cpc"]
    value: str


class ParagraphFilter(BaseModel):
    kind: Literal["paragraph"]
    value: str


QueryFilter = Annotated[
    Union[SectionFilter, ContainsFilter, MetadataFilter, CpcFilter, ParagraphFilter],
    Field(discriminator="kind"),
]


class QueryClause(BaseModel):
    filter: QueryFilter
    negated: bool = False


class FilterExpression(BaseModel):
    kind: Literal["filter"]
    filter: QueryFilter


class NotExpression(BaseModel):
    kind: Literal["not"]
    expression: "QueryExpression"


class AndExpression(BaseModel):
    kind: Literal["and"]
    expressions: list["QueryExpression"]


class OrExpression(BaseModel):
    kind: Literal["or"]
    expressions: list["QueryExpression"]


QueryExpression = Annotated[
    Union[FilterExpression, NotExpression, AndExpression, OrExpression],
    Field(discriminator="kind"),
]


class Query(BaseModel):
    filters: list[QueryFilter] = Field(default_factory=list)
    groups: list[list[QueryClause]] | None = None
    expression: QueryExpression | None = None

    @model_validator(mode="after")
    def normalize_groups(self) -> "Query":
        if self.expression is None and self.groups is None:
            self.groups = [[QueryClause(filter=query_filter) for query_filter in self.filters]]
            self.expression = _groups_to_expression(self.groups)
        elif self.expression is None and self.groups is not None:
            self.expression = _groups_to_expression(self.groups)
        elif self.expression is not None and self.groups is None:
            self.groups = _expression_to_groups(self.expression)

        if not self.filters and self.groups:
            self.filters = [clause.filter for group in self.groups for clause in group if not clause.negated]

        if not self.groups or any(not group for group in self.groups):
            raise ValueError("Query requires at least one filter.")

        return self


class QueryMatch(BaseModel):
    passageId: str
    documentId: str
    sectionType: SectionType
    sectionTitle: str
    passageIndex: int
    passageText: str
    contextBefore: str | None
    contextAfter: str | None
    reasons: list[str]
    paragraphId: str | None = None
    claimNo: int | None = None


class QueryResult(BaseModel):
    totalMatches: int
    matches: list[QueryMatch]


class QueryRequest(BaseModel):
    documentIds: list[str] = Field(default_factory=list)
    documentId: str | None = None
    queryText: str

    @model_validator(mode="after")
    def normalize_document_ids(self) -> "QueryRequest":
        if not self.documentIds and self.documentId:
            self.documentIds = [self.documentId]

        if not self.documentIds:
            raise ValueError("Select at least one document.")

        return self


class ParseDocumentRequest(BaseModel):
    fileName: str


class PreloadDocumentsRequest(BaseModel):
    documentIds: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_document_ids(self) -> "PreloadDocumentsRequest":
        seen: set[str] = set()
        self.documentIds = [document_id for document_id in self.documentIds if not (document_id in seen or seen.add(document_id))]
        return self


def _groups_to_expression(groups: list[list[QueryClause]]) -> QueryExpression:
    group_expressions: list[QueryExpression] = []
    for group in groups:
        expressions = [_clause_to_expression(clause) for clause in group]
        group_expressions.append(expressions[0] if len(expressions) == 1 else AndExpression(kind="and", expressions=expressions))

    return group_expressions[0] if len(group_expressions) == 1 else OrExpression(kind="or", expressions=group_expressions)


def _clause_to_expression(clause: QueryClause) -> QueryExpression:
    expression: QueryExpression = FilterExpression(kind="filter", filter=clause.filter)
    return NotExpression(kind="not", expression=expression) if clause.negated else expression


def _expression_to_groups(expression: QueryExpression) -> list[list[QueryClause]]:
    # Compatibility projection for callers that still inspect the old OR-of-ANDs
    # fields. Nested expressions that cannot be represented exactly are flattened
    # to their leaf clauses, while execution uses the expression tree.
    if isinstance(expression, OrExpression):
        return [_expression_to_clauses(child) for child in expression.expressions]

    return [_expression_to_clauses(expression)]


def _expression_to_clauses(expression: QueryExpression, negated: bool = False) -> list[QueryClause]:
    if isinstance(expression, FilterExpression):
        return [QueryClause(filter=expression.filter, negated=negated)]

    if isinstance(expression, NotExpression):
        return _expression_to_clauses(expression.expression, not negated)

    clauses: list[QueryClause] = []
    if isinstance(expression, (AndExpression, OrExpression)):
        for child in expression.expressions:
            clauses.extend(_expression_to_clauses(child, negated))

    return clauses


def coerce_section_type(raw: str) -> SectionType | None:
    return SECTION_SYNONYMS.get(raw.strip().upper())


def infer_section_type(heading: str) -> SectionType:
    normalized = heading.strip().upper()

    if "CLAIM" in normalized:
        return "CLAIMS"
    if "ABSTRACT" in normalized:
        return "ABSTRACT"
    if (
        "SPECIFICATION" in normalized
        or "DESCRIPTION" in normalized
        or "BACKGROUND" in normalized
        or "SUMMARY" in normalized
        or "FIELD" in normalized
    ):
        return "SPECIFICATION"
    if "TITLE" in normalized:
        return "TITLE"

    return "OTHER"
