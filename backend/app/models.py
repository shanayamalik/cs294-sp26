from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

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


class Section(BaseModel):
    type: SectionType
    title: str
    passages: list[Passage]


class DocumentMetadata(BaseModel):
    id: str
    title: str
    sourceFile: str
    ingestedAt: str


class Document(BaseModel):
    metadata: DocumentMetadata
    sections: list[Section]


class SectionFilter(BaseModel):
    kind: Literal["section"]
    value: SectionType


class ContainsFilter(BaseModel):
    kind: Literal["contains"]
    value: str


QueryFilter = Annotated[Union[SectionFilter, ContainsFilter], Field(discriminator="kind")]


class Query(BaseModel):
    filters: list[QueryFilter]


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


class QueryResult(BaseModel):
    totalMatches: int
    matches: list[QueryMatch]


class QueryRequest(BaseModel):
    documentId: str
    queryText: str


class ParseDocumentRequest(BaseModel):
    fileName: str


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
