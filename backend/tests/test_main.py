from pathlib import Path

import app.main as main_module
from app import synonym_sets
from app.dsl_parser import parse_dsl
from app.models import Document, DocumentMetadata, Passage, PreloadDocumentsRequest, Section
from app.store import DocumentStore


def setup_function() -> None:
    synonym_sets.clear_saved_termsets()


def test_preload_endpoint_hydrates_selected_documents(tmp_path: Path, monkeypatch) -> None:
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    document = _document("alpha", "Alpha Patent")
    (parsed_dir / "alpha.json").write_text(document.model_dump_json(exclude_none=True), encoding="utf-8")

    store = DocumentStore()
    monkeypatch.setattr(main_module, "store", store)
    monkeypatch.setattr(main_module, "PARSED_DATA_DIR", parsed_dir)

    main_module.startup()
    payload = main_module.preload_documents(PreloadDocumentsRequest(documentIds=["alpha", "alpha"]))

    assert payload["requestedDocuments"] == 1
    assert payload["preloadedDocuments"] == 1
    assert payload["stats"]["cachedDocuments"] == 1
    assert payload["stats"]["lazyLoads"] == 1


def test_query_synonym_sets_endpoint_has_no_fixed_builtin_catalog() -> None:
    payload = main_module.query_synonym_sets()

    assert payload["synonymSets"] == []


def test_query_handler_supports_synonym_of(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(synonym_sets, "_fetch_datamuse_synonyms", lambda seed, max_results, topics: ("hypervisor",))

    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    document = _document("alpha", "Alpha Patent")
    document.sections[0].passages[0].text = "A hypervisor manages virtualized resources."
    (parsed_dir / "alpha.json").write_text(document.model_dump_json(exclude_none=True), encoding="utf-8")

    store = DocumentStore()
    monkeypatch.setattr(main_module, "store", store)
    monkeypatch.setattr(main_module, "PARSED_DATA_DIR", parsed_dir)

    main_module.startup()
    payload = main_module.run_query(main_module.QueryRequest(documentIds=["alpha"], queryText='synonym_of:"virtual machine"'))

    assert payload["result"]["totalMatches"] == 1
    assert any('hypervisor' in reason for reason in payload["result"]["matches"][0]["reasons"])
    assert payload["synonymExpansions"] == [
        {
            "seed": "virtual machine",
            "terms": ["virtual machine", "hypervisor"],
            "max": synonym_sets.DATAMUSE_MAX_RESULTS,
            "topics": synonym_sets.DATAMUSE_TOPICS,
        }
    ]

    termset_payload = main_module.run_query(main_module.QueryRequest(documentIds=["alpha"], queryText='termset:"virtual machine"'))

    assert termset_payload["result"]["totalMatches"] == 1
    assert termset_payload["synonymExpansions"] == []
    assert main_module.query_synonym_sets()["synonymSets"] == [
        {"seed": "virtual machine", "terms": ["virtual machine", "hypervisor"]}
    ]


def test_documents_endpoint_includes_metadata_facet_summaries(tmp_path: Path, monkeypatch) -> None:
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    document = _document(
        "alpha",
        "Alpha Patent",
        assignee={"name": "Example Corp", "city": "San Jose"},
        inventors=[{"nameAndCity": "Anderson; Evan K. Seattle", "country": "US"}],
    )
    (parsed_dir / "alpha.json").write_text(document.model_dump_json(exclude_none=True), encoding="utf-8")

    store = DocumentStore()
    monkeypatch.setattr(main_module, "store", store)
    monkeypatch.setattr(main_module, "PARSED_DATA_DIR", parsed_dir)

    main_module.startup()
    payload = main_module.documents()

    assert payload["documents"] == [
        {
            "id": "alpha",
            "title": "Alpha Patent",
            "sourceFile": "alpha.txt",
            "ingestedAt": "2026-05-13T00:00:00Z",
            "assigneeName": "Example Corp",
            "inventorNames": ["Anderson; Evan K. Seattle"],
        }
    ]


def _document(
    document_id: str,
    title: str,
    *,
    assignee: dict[str, str] | None = None,
    inventors: list[dict[str, str]] | None = None,
) -> Document:
    return Document(
        metadata=DocumentMetadata(
            id=document_id,
            title=title,
            sourceFile=f"{document_id}.txt",
            ingestedAt="2026-05-13T00:00:00Z",
            assignee=assignee,
            inventors=inventors,
        ),
        sections=[
            Section(
                type="SPECIFICATION",
                title="Specification",
                passages=[
                    Passage(
                        id=f"{document_id}-p1",
                        text=f"{document_id} passage",
                        index=0,
                        sectionType="SPECIFICATION",
                        startOffset=0,
                        endOffset=10,
                    )
                ],
            )
        ],
    )
