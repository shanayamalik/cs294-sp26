from datetime import datetime, timezone

from app.models import Document, DocumentMetadata, Passage, Query, Section, SectionFilter, ContainsFilter
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
