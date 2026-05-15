from app import synonym_sets
from app.dsl_parser import parse_dsl


def setup_function() -> None:
    synonym_sets.clear_saved_termsets()


def test_parse_section_contains_query() -> None:
    query = parse_dsl('section:SPECIFICATION AND contains:"signal processing"')

    assert len(query.filters) == 2
    assert query.filters[0].kind == "section"
    assert query.filters[0].value == "SPECIFICATION"
    assert query.filters[1].kind == "contains"
    assert query.filters[1].value == "signal processing"
    assert query.filters[1].mode == "literal"


def test_parse_granular_section_query() -> None:
    query = parse_dsl('section:BACKGROUND AND contains:"signal processing"')

    assert len(query.filters) == 2
    assert query.filters[0].kind == "section"
    assert query.filters[0].value == "BACKGROUND"


def test_parse_contains_regex_query() -> None:
    query = parse_dsl(r'contains.regex:"signal\s+processing"')

    assert len(query.filters) == 1
    assert query.filters[0].kind == "contains"
    assert query.filters[0].value == r"signal\s+processing"
    assert query.filters[0].mode == "regex"


def test_parse_heading_query() -> None:
    query = parse_dsl('heading:"Detailed Description"')

    assert len(query.filters) == 1
    assert query.filters[0].kind == "heading"
    assert query.filters[0].value == "Detailed Description"


def test_parse_section_title_alias_query() -> None:
    query = parse_dsl('sectionTitle:"Background of the Invention"')

    assert len(query.filters) == 1
    assert query.filters[0].kind == "heading"
    assert query.filters[0].value == "Background of the Invention"


def test_parse_synonym_of_query_expands_to_contains_or_expression(monkeypatch) -> None:
    monkeypatch.setattr(
        synonym_sets,
        "_fetch_datamuse_synonyms",
        lambda seed, max_results, topics: ("hypervisor", "guest operating system", "virtual machine"),
    )

    query = parse_dsl('synonym_of:"virtual machine"')

    assert query.expression is not None
    assert query.expression.kind == "or"
    assert {query_filter.value for query_filter in query.filters if query_filter.kind == "contains"} == {
        "virtual machine",
        "hypervisor",
        "guest operating system",
    }
    assert synonym_sets.expand_termset("virtual machine") == [
        "virtual machine",
        "hypervisor",
        "guest operating system",
    ]
    assert query.synonymExpansions[0].model_dump() == {
        "seed": "virtual machine",
        "terms": ["virtual machine", "hypervisor", "guest operating system"],
        "max": synonym_sets.DATAMUSE_MAX_RESULTS,
        "topics": synonym_sets.DATAMUSE_TOPICS,
    }


def test_parse_synonym_of_query_supports_max_and_topics_options(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_fetch(seed: str, max_results: int, topics: str) -> tuple[str, ...]:
        captured["seed"] = seed
        captured["max"] = max_results
        captured["topics"] = topics
        return ("hypervisor",)

    monkeypatch.setattr(synonym_sets, "_fetch_datamuse_synonyms", fake_fetch)

    query = parse_dsl('synonym_of:"virtual machine"|max=3|topics="cloud computing patents"')

    assert {query_filter.value for query_filter in query.filters if query_filter.kind == "contains"} == {
        "virtual machine",
        "hypervisor",
    }
    assert captured == {"seed": "virtual machine", "max": 3, "topics": "cloud computing patents"}
    assert query.synonymExpansions[0].model_dump() == {
        "seed": "virtual machine",
        "terms": ["virtual machine", "hypervisor"],
        "max": 3,
        "topics": "cloud computing patents",
    }


def test_parse_synonym_of_rejects_unsupported_options() -> None:
    try:
        parse_dsl('synonym_of:"virtual machine"|mode=rel_syn')
        raise AssertionError("Expected parse_dsl to raise ValueError")
    except ValueError as error:
        assert "Unsupported synonym_of option: mode" in str(error)


def test_parse_synonym_of_rejects_invalid_max() -> None:
    try:
        parse_dsl('synonym_of:"virtual machine"|max=0')
        raise AssertionError("Expected parse_dsl to raise ValueError")
    except ValueError as error:
        assert "synonym_of max option must be a positive integer." in str(error)


def test_parse_termset_query_expands_saved_synonyms_to_contains_or_expression(monkeypatch) -> None:
    monkeypatch.setattr(
        synonym_sets,
        "_fetch_datamuse_synonyms",
        lambda seed, max_results, topics: ("forwarding table", "fib", "routing cache"),
    )

    parse_dsl('synonym_of:"routing table"')
    query = parse_dsl('termset:"routing table"')

    assert query.expression is not None
    assert query.expression.kind == "or"
    assert {query_filter.value for query_filter in query.filters if query_filter.kind == "contains"} == {
        "routing table",
        "forwarding table",
        "fib",
        "routing cache",
    }


def test_parse_synonym_of_datamuse_failure_raises_helpful_error(monkeypatch) -> None:
    def fail_fetch(seed: str, max_results: int, topics: str) -> tuple[str, ...]:
        raise ValueError(f'Unable to fetch synonyms for "{seed}" from Datamuse.')

    monkeypatch.setattr(synonym_sets, "_fetch_datamuse_synonyms", fail_fetch)

    try:
        parse_dsl('synonym_of:"unknown term"')
        raise AssertionError("Expected parse_dsl to raise ValueError")
    except ValueError as error:
        assert 'Unable to fetch synonyms for "unknown term" from Datamuse.' in str(error)


def test_parse_termset_unknown_seed_raises_helpful_error() -> None:
    try:
        parse_dsl('termset:"unknown term"')
        raise AssertionError("Expected parse_dsl to raise ValueError")
    except ValueError as error:
        assert 'Unknown termset: "unknown term"' in str(error)
        assert 'Run synonym_of:"unknown term" first' in str(error)


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


def test_parse_claim_query() -> None:
    query = parse_dsl("claim:8")

    assert len(query.filters) == 1
    assert query.filters[0].kind == "claim"
    assert query.filters[0].value == 8


def test_parse_figure_query() -> None:
    query = parse_dsl('figure:"FIG. 2"')

    assert len(query.filters) == 1
    assert query.filters[0].kind == "figure"
    assert query.filters[0].value == "FIG. 2"
