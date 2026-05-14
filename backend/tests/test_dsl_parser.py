from app.dsl_parser import parse_dsl


def test_parse_section_contains_query() -> None:
    query = parse_dsl('section:SPECIFICATION AND contains:"signal processing"')

    assert len(query.filters) == 2
    assert query.filters[0].kind == "section"
    assert query.filters[0].value == "SPECIFICATION"
    assert query.filters[1].kind == "contains"
    assert query.filters[1].value == "signal processing"
    assert query.filters[1].mode == "literal"


def test_parse_contains_regex_query() -> None:
    query = parse_dsl(r'contains.regex:"signal\s+processing"')

    assert len(query.filters) == 1
    assert query.filters[0].kind == "contains"
    assert query.filters[0].value == r"signal\s+processing"
    assert query.filters[0].mode == "regex"


def test_parse_unsupported_clause() -> None:
    try:
        parse_dsl("rank:semantic")
        raise AssertionError("Expected parse_dsl to raise ValueError")
    except ValueError as error:
        assert "Unsupported clause" in str(error)


def test_parse_metadata_comparison_query() -> None:
    query = parse_dsl("meta.filingDate:<2018-03-15")

    assert len(query.filters) == 1
    assert query.filters[0].kind == "metadata"
    assert query.filters[0].field == "filingDate"
    assert query.filters[0].operator == "lt"
    assert query.filters[0].value == "2018-03-15"


def test_parse_metadata_contains_query() -> None:
    query = parse_dsl('meta.assignee.name:~"Google"')

    assert len(query.filters) == 1
    assert query.filters[0].kind == "metadata"
    assert query.filters[0].field == "assignee.name"
    assert query.filters[0].operator == "contains"
    assert query.filters[0].value == "Google"


def test_parse_metadata_alias_query() -> None:
    query = parse_dsl("meta.pubDate:>=2019-01-01")

    assert len(query.filters) == 1
    assert query.filters[0].kind == "metadata"
    assert query.filters[0].field == "pubDate"
    assert query.filters[0].operator == "gte"
    assert query.filters[0].value == "2019-01-01"


def test_parse_metadata_date_convenience_alias_query() -> None:
    query = parse_dsl("meta.appDate:=20110719")

    assert len(query.filters) == 1
    assert query.filters[0].kind == "metadata"
    assert query.filters[0].field == "appDate"
    assert query.filters[0].operator == "eq"
    assert query.filters[0].value == "20110719"


def test_parse_metadata_priority_helper_query() -> None:
    query = parse_dsl("meta.priorityDate:<2011-07-01")

    assert len(query.filters) == 1
    assert query.filters[0].kind == "metadata"
    assert query.filters[0].field == "priorityDate"
    assert query.filters[0].operator == "lt"
    assert query.filters[0].value == "2011-07-01"
