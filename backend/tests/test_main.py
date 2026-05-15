from pathlib import Path

import app.main as main_module
from app.dsl_parser import parse_dsl
from app.models import Document, DocumentMetadata, Passage, PreloadDocumentsRequest, Section
from app.store import DocumentStore


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


def test_query_synonym_sets_endpoint_lists_available_builtins() -> None:
    payload = main_module.query_synonym_sets()

    assert payload["synonymSets"]
    assert payload["synonymSets"][0]["seed"] in {"routing table", "virtual machine"}


def test_query_handler_supports_synonym_of(tmp_path: Path, monkeypatch) -> None:
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