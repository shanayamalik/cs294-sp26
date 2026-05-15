from datetime import datetime, timezone

from app.models import ClaimFilter, ContainsFilter, Document, DocumentMetadata, FigureFilter, MetadataFilter, Passage, Query, Section, SectionFilter
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


def test_execute_query_specification_filter_matches_granular_sections() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
        ),
        sections=[
            Section(
                type="BACKGROUND",
                title="BACKGROUND OF THE INVENTION",
                passages=[
                    Passage(
                        id="p1",
                        text="Background signal processing context.",
                        index=0,
                        sectionType="BACKGROUND",
                        startOffset=0,
                        endOffset=37,
                    )
                ],
            ),
            Section(
                type="DESCRIPTION",
                title="DETAILED DESCRIPTION",
                passages=[
                    Passage(
                        id="p2",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="DESCRIPTION",
                        startOffset=0,
                        endOffset=50,
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

    assert result.totalMatches == 2
    assert {match.passageId for match in result.matches} == {"p1", "p2"}


def test_execute_query_background_filter_is_more_specific() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
        ),
        sections=[
            Section(
                type="BACKGROUND",
                title="BACKGROUND OF THE INVENTION",
                passages=[
                    Passage(
                        id="p1",
                        text="Background signal processing context.",
                        index=0,
                        sectionType="BACKGROUND",
                        startOffset=0,
                        endOffset=37,
                    )
                ],
            ),
            Section(
                type="DESCRIPTION",
                title="DETAILED DESCRIPTION",
                passages=[
                    Passage(
                        id="p2",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="DESCRIPTION",
                        startOffset=0,
                        endOffset=50,
                    )
                ],
            ),
        ],
    )

    query = Query(
        filters=[
            SectionFilter(kind="section", value="BACKGROUND"),
            ContainsFilter(kind="contains", value="signal processing"),
        ]
    )

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p1"


def test_execute_query_contains_supports_regex() -> None:
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
                        text="A Signal    processing module receives sensor data.",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=55,
                    ),
                    Passage(
                        id="p2",
                        text="Calibration updates are applied once per cycle.",
                        index=1,
                        sectionType="SPECIFICATION",
                        startOffset=56,
                        endOffset=105,
                    ),
                ],
            )
        ],
    )

    query = Query(filters=[ContainsFilter(kind="contains", value=r"signal\s+processing", mode="regex")])

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p1"
    assert r'Matched contains.regex:"signal\s+processing"' in result.matches[0].reasons


def test_execute_query_plain_contains_does_not_interpret_regex() -> None:
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
                        text="A Signal    processing module receives sensor data.",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=55,
                    )
                ],
            )
        ],
    )

    query = Query(filters=[ContainsFilter(kind="contains", value=r"signal\s+processing")])

    result = execute_query(fixture, query)

    assert result.totalMatches == 0


def test_execute_query_contains_keeps_literal_phrase_behavior_for_regex_punctuation() -> None:
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
                        text="The C++ module receives sensor data.",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=36,
                    ),
                    Passage(
                        id="p2",
                        text="The Python module receives sensor data.",
                        index=1,
                        sectionType="SPECIFICATION",
                        startOffset=37,
                        endOffset=76,
                    ),
                ],
            )
        ],
    )

    query = Query(filters=[ContainsFilter(kind="contains", value="C++")])

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p1"


def test_execute_query_contains_ignores_invalid_regex_when_literal_does_not_match() -> None:
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
                    )
                ],
            )
        ],
    )

    query = Query(filters=[ContainsFilter(kind="contains", value="[", mode="regex")])

    result = execute_query(fixture, query)

    assert result.totalMatches == 0


def test_execute_query_claim_filter_matches_claim_number() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
        ),
        sections=[
            Section(
                type="CLAIMS",
                title="CLAIMS",
                passages=[
                    Passage(
                        id="p1",
                        text="1. A system comprising a processor.",
                        index=0,
                        sectionType="CLAIMS",
                        startOffset=0,
                        endOffset=35,
                        claimNo=1,
                    ),
                    Passage(
                        id="p2",
                        text="2. The system of claim 1, wherein the processor updates calibration parameters.",
                        index=1,
                        sectionType="CLAIMS",
                        startOffset=36,
                        endOffset=114,
                        claimNo=2,
                    ),
                ],
            )
        ],
    )

    query = Query(filters=[ClaimFilter(kind="claim", value=2)])

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p2"
    assert result.matches[0].claimNo == 2
    assert "Matched claim:2" in result.matches[0].reasons


def test_execute_query_figure_filter_matches_normalized_figure_reference() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
        ),
        sections=[
            Section(
                type="DESCRIPTION",
                title="DETAILED DESCRIPTION",
                passages=[
                    Passage(
                        id="p1",
                        text="FIG. 2 shows the provisioning workflow.",
                        index=0,
                        sectionType="DESCRIPTION",
                        startOffset=0,
                        endOffset=38,
                        figureRefs=["FIG. 2"],
                    ),
                    Passage(
                        id="p2",
                        text="FIG. 3 shows the deployment flow.",
                        index=1,
                        sectionType="DESCRIPTION",
                        startOffset=39,
                        endOffset=74,
                        figureRefs=["FIG. 3"],
                    ),
                ],
            )
        ],
    )

    query = Query(filters=[FigureFilter(kind="figure", value="fig 2")])

    result = execute_query(fixture, query)

    assert result.totalMatches == 1
    assert result.matches[0].passageId == "p1"
    assert result.matches[0].figureRefs == ["FIG. 2"]
    assert 'Matched figure:"fig 2"' in result.matches[0].reasons


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
    publication_convenience_query = Query(filters=[MetadataFilter(kind="metadata", field="published", operator="gte", value="2019-01-01")])
    application_query = Query(filters=[MetadataFilter(kind="metadata", field="appNo", operator="eq", value="12/345678")])
    filing_convenience_query = Query(filters=[MetadataFilter(kind="metadata", field="filing", operator="lt", value="2018-03-15")])
    filing_query = Query(filters=[MetadataFilter(kind="metadata", field="filed", operator="lt", value="2018-03-15")])
    app_date_query = Query(filters=[MetadataFilter(kind="metadata", field="appDate", operator="eq", value="20110719")])
    app_filed_query = Query(filters=[MetadataFilter(kind="metadata", field="appFiled", operator="eq", value="20110719")])

    assert execute_query(fixture, publication_query).totalMatches == 1
    assert execute_query(fixture, publication_convenience_query).totalMatches == 1
    assert execute_query(fixture, application_query).totalMatches == 1
    assert execute_query(fixture, filing_convenience_query).totalMatches == 1
    assert execute_query(fixture, filing_query).totalMatches == 1
    assert execute_query(fixture, app_date_query).totalMatches == 1
    assert execute_query(fixture, app_filed_query).totalMatches == 1


def test_execute_query_inventor_and_assignee_name_aliases() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
            inventors=[{"nameAndCity": "Anderson; Evan K. Seattle", "country": "US"}],
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

    assignee_query = Query(filters=[MetadataFilter(kind="metadata", field="assigneeName", operator="contains", value="Google")])
    inventor_query = Query(filters=[MetadataFilter(kind="metadata", field="inventorName", operator="startswith", value="Anderson")])

    assert execute_query(fixture, assignee_query).totalMatches == 1
    assert execute_query(fixture, inventor_query).totalMatches == 1


def test_execute_query_priority_and_admissibility_helpers() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
            filingDate="2011-07-19",
            applicationFilingDate="20110719",
            domesticPriority=["us-provisional-application US 61492708 20110602"],
        ),
        sections=[
            Section(
                type="ABSTRACT",
                title="Abstract",
                passages=[
                    Passage(
                        id="p1",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="ABSTRACT",
                        startOffset=0,
                        endOffset=50,
                    )
                ],
            )
        ],
    )

    priority_query = Query(filters=[MetadataFilter(kind="metadata", field="priorityDate", operator="lt", value="2011-07-01")])
    effective_query = Query(filters=[MetadataFilter(kind="metadata", field="effectiveDate", operator="lt", value="2011-07-01")])
    admissibility_query = Query(filters=[MetadataFilter(kind="metadata", field="admissibilityDate", operator="lt", value="2011-07-01")])

    assert execute_query(fixture, priority_query).totalMatches == 1
    assert execute_query(fixture, effective_query).totalMatches == 1
    assert execute_query(fixture, admissibility_query).totalMatches == 1


def test_execute_query_effective_date_falls_back_without_priority_claim() -> None:
    fixture = Document(
        metadata=DocumentMetadata(
            id="doc-1",
            title="Sample",
            sourceFile="sample.txt",
            ingestedAt=datetime.now(timezone.utc).isoformat(),
            filingDate="2011-07-19",
            applicationFilingDate="20110719",
        ),
        sections=[
            Section(
                type="ABSTRACT",
                title="Abstract",
                passages=[
                    Passage(
                        id="p1",
                        text="A signal processing module receives sensor data.",
                        index=0,
                        sectionType="ABSTRACT",
                        startOffset=0,
                        endOffset=50,
                    )
                ],
            )
        ],
    )

    effective_query = Query(filters=[MetadataFilter(kind="metadata", field="effectiveDate", operator="eq", value="2011-07-19")])

    assert execute_query(fixture, effective_query).totalMatches == 1
