from pathlib import Path

import app.main as main_module
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


def _document(document_id: str, title: str) -> Document:
    return Document(
        metadata=DocumentMetadata(
            id=document_id,
            title=title,
            sourceFile=f"{document_id}.txt",
            ingestedAt="2026-05-13T00:00:00Z",
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