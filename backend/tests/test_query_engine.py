from datetime import datetime, timezone

from app.models import ContainsFilter, Document, DocumentMetadata, MetadataFilter, Passage, Query, Section, SectionFilter
from app.query_engine import execute_query


def test_execute_query_section_and_contains() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
        ),
        sections=[
            Section(
                type="SPECIFICATION",
                title="DETAILED DESCRIPTION",
                passages=[
                    Passage(
                        id="p1",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=50,
                    ),
                    Passage(
                        id="p2",
                        text="Calibration updates are applied once per cycle.",
                        index=1,
                        sectionType="SPECIFICATION",
                        startOffset=51,
                        endOffset=100,
                    ),
                ],
            ),
            Section(
                type="CLAIMS",
                title="CLAIMS",
                passages=[
                    Passage(
                        id="p3",
                        text="1. A system comprising a processor.",
                        index=0,
                        sectionType="CLAIMS",
                        startOffset=0,
                        endOffset=35,
                    )
                ],
            ),
        ],
    )

    query = Query(
        filters=[
            SectionFilter(kind="section", value="SPECIFICATION"),
            ContainsFilter(kind="contains", value="signal processing"),
        ]
    )

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p1"
    assert "Matched section:SPECIFICATION" in result.matches[0].reasons


def test_execute_query_metadata_date_comparison() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
            filingDate="2011-07-19",
        ),
        sections=[
            Section(
                type="SPECIFICATION",
                title="DETAILED DESCRIPTION",
                passages=[
                    Passage(
                        id="p1",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=50,
                    )
                ],
            )
        ],
    )

    query = Query(filters=[MetadataFilter(kind="metadata", field="filingDate", operator="lt", value="2018-03-15")])

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p1"
    assert 'Matched meta.filingDate:<"2018-03-15"' in result.matches[0].reasons


def test_execute_query_metadata_contains_nested_field() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
            assignee={"name": "Google LLC", "city": "Mountain View"},
        ),
        sections=[
            Section(
                type="SPECIFICATION",
                title="DETAILED DESCRIPTION",
                passages=[
                    Passage(
                        id="p1",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=50,
                    )
                ],
            )
        ],
    )

    query = Query(filters=[MetadataFilter(kind="metadata", field="assignee.name", operator="contains", value="Google")])

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p1"
    assert 'Matched meta.assignee.name:~"Google"' in result.matches[0].reasons


def test_execute_query_metadata_aliases() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
            publicationDate="2021-09-28",
            applicationNo="12/345678",
            filingDate="2011-07-19",
            applicationFilingDate="20110719",
        ),
        sections=[
            Section(
                type="SPECIFICATION",
                title="DETAILED DESCRIPTION",
                passages=[
                    Passage(
                        id="p1",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=50,
                    )
                ],
            )
        ],
    )

    publication_query = Query(filters=[MetadataFilter(kind="metadata", field="pubDate", operator="gte", value="2019-01-01")])
    application_query = Query(filters=[MetadataFilter(kind="metadata", field="appNo", operator="eq", value="12/345678")])
    filing_query = Query(filters=[MetadataFilter(kind="metadata", field="filed", operator="lt", value="2018-03-15")])
    app_filed_query = Query(filters=[MetadataFilter(kind="metadata", field="appFiled", operator="eq", value="20110719")])

    assert execute_query(fixture, publication_query).totalMatches == 1
    assert execute_query(fixture, application_query).totalMatches == 1
    assert execute_query(fixture, filing_query).totalMatches == 1
    assert execute_query(fixture, app_filed_query).totalMatches == 1
