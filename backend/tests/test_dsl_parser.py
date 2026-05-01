from app.dsl_parser import parse_dsl


def test_parse_section_contains_query() -> None:
    query = parse_dsl('section:SPECIFICATION AND contains:"signal processing"')

    assert len(query.filters) == 2
    assert query.filters[0].kind == "section"
    assert query.filters[0].value == "SPECIFICATION"
    assert query.filters[1].kind == "contains"
    assert query.filters[1].value == "signal processing"


def test_parse_unsupported_clause() -> None:
    try:
        parse_dsl("rank:semantic")
        raise AssertionError("Expected parse_dsl to raise ValueError")
    except ValueError as error:
        assert "Unsupported clause" in str(error)
