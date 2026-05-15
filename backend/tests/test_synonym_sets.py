from app import synonym_sets


def setup_function() -> None:
    synonym_sets.clear_saved_termsets()


def test_expand_synonym_seed_fetches_datamuse_terms(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args) -> None:
            return None

        def read(self) -> bytes:
            return b'[{"word":"Hypervisor"},{"word":"virtual machine"},{"score":99}]'

    def fake_urlopen(url: str, timeout: float) -> Response:
        captured["url"] = url
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(synonym_sets, "urlopen", fake_urlopen)

    terms = synonym_sets.expand_synonym_seed(" Virtual   Machine ")

    assert terms == ["virtual machine", "hypervisor"]
    assert captured["timeout"] == synonym_sets.DATAMUSE_TIMEOUT_SECONDS
    assert "ml=virtual+machine" in str(captured["url"])
    assert "max=10" in str(captured["url"])
    assert "topics=computer+science+software+electrical+engineering" in str(captured["url"])


def test_expanded_synonyms_are_saved_as_termsets(monkeypatch) -> None:
    monkeypatch.setattr(synonym_sets, "_fetch_datamuse_synonyms", lambda seed, max_results, topics: ("hypervisor",))

    assert synonym_sets.expand_synonym_seed("virtual machine") == ["virtual machine", "hypervisor"]
    assert synonym_sets.expand_termset(" Virtual   Machine ") == ["virtual machine", "hypervisor"]
    assert synonym_sets.synonym_seed_summaries() == [
        {"seed": "virtual machine", "terms": ["virtual machine", "hypervisor"]}
    ]


def test_expand_synonym_seed_honors_max_and_topics(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_fetch(seed: str, max_results: int, topics: str) -> tuple[str, ...]:
        captured["seed"] = seed
        captured["max"] = max_results
        captured["topics"] = topics
        return ("hypervisor",)

    monkeypatch.setattr(synonym_sets, "_fetch_datamuse_synonyms", fake_fetch)

    assert synonym_sets.expand_synonym_seed("virtual machine", max_results=3, topics="cloud patents") == [
        "virtual machine",
        "hypervisor",
    ]
    assert captured == {"seed": "virtual machine", "max": 3, "topics": "cloud patents"}


def test_expand_synonym_seed_replaces_saved_termset_only_when_terms_change(monkeypatch) -> None:
    calls = iter([("hypervisor",), ("hypervisor",), ("guest os",)])
    monkeypatch.setattr(synonym_sets, "_fetch_datamuse_synonyms", lambda seed, max_results, topics: next(calls))

    first_terms = synonym_sets.expand_synonym_seed("virtual machine")
    first_saved = synonym_sets.TERMSETS["virtual machine"]

    assert synonym_sets.expand_synonym_seed("virtual machine") == first_terms
    assert synonym_sets.TERMSETS["virtual machine"] is first_saved

    assert synonym_sets.expand_synonym_seed("virtual machine") == ["virtual machine", "guest os"]
    assert synonym_sets.TERMSETS["virtual machine"] is not first_saved
