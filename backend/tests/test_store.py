from pathlib import Path

from app.models import Document, DocumentMetadata, Passage, Section
from app.store import DocumentStore, _metadata_sidecar_path


def test_load_from_parsed_dir_lists_without_eager_document_hydration(tmp_path: Path) -> None:
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()

    first = _document("alpha", "Alpha Patent")
    second = _document("beta", "Beta Patent")

    (parsed_dir / "alpha.json").write_text(first.model_dump_json(exclude_none=True), encoding="utf-8")
    (parsed_dir / "beta.json").write_text(second.model_dump_json(exclude_none=True), encoding="utf-8")

    store = DocumentStore()
    store.load_from_parsed_dir(parsed_dir)

    assert store.list() == [
        {
            "id": "alpha",
            "title": "Alpha Patent",
            "sourceFile": "alpha.txt",
            "ingestedAt": "2026-05-13T00:00:00Z",
            "assigneeName": None,
            "inventorNames": None,
        },
        {
            "id": "beta",
            "title": "Beta Patent",
            "sourceFile": "beta.txt",
            "ingestedAt": "2026-05-13T00:00:00Z",
            "assigneeName": None,
            "inventorNames": None,
        },
    ]
    assert store._by_id == {}
    assert store.stats()["indexedDocuments"] == 2
    assert store.stats()["cachedDocuments"] == 0
    assert store.stats()["lazyLoads"] == 0

    loaded = store.get("alpha")

    assert loaded is not None
    assert loaded.metadata.id == "alpha"
    assert loaded.sections[0].passages[0].text == "alpha passage"
    assert "alpha" in store._by_id
    assert store.stats()["lazyLoads"] == 1
    assert store.stats()["cachedDocuments"] == 1

    loaded_again = store.get("alpha")

    assert loaded_again is loaded
    assert store.stats()["cacheHits"] == 1


def test_upsert_keeps_list_metadata_in_sync() -> None:
    store = DocumentStore()
    document = _document("gamma", "Gamma Patent")

    store.upsert(document)

    assert store.list() == [
        {
            "id": "gamma",
            "title": "Gamma Patent",
            "sourceFile": "gamma.txt",
            "ingestedAt": "2026-05-13T00:00:00Z",
            "assigneeName": None,
            "inventorNames": None,
        }
    ]
    assert store.get("gamma") is document
    assert store.stats()["cachedDocuments"] == 1
    assert store.stats()["indexedDocuments"] == 1


def test_write_document_creates_metadata_sidecar(tmp_path: Path) -> None:
    store = DocumentStore()
    document = _document("delta", "Delta Patent")

    out_path = store.write_document(tmp_path, document)

    metadata_path = _metadata_sidecar_path(out_path)
    assert metadata_path.exists()
    metadata = DocumentMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
    assert metadata.id == "delta"


def test_list_includes_assignee_and_inventor_summaries() -> None:
    store = DocumentStore()
    document = _document(
        "epsilon",
        "Epsilon Patent",
        assignee={"name": "Example Corp", "city": "San Jose"},
        inventors=[
            {"nameAndCity": "Anderson; Evan K. Seattle", "country": "US"},
            {"nameAndCity": "Patel; Rina Mountain View", "country": "US"},
        ],
    )

    store.upsert(document)

    assert store.list() == [
        {
            "id": "epsilon",
            "title": "Epsilon Patent",
            "sourceFile": "epsilon.txt",
            "ingestedAt": "2026-05-13T00:00:00Z",
            "assigneeName": "Example Corp",
            "inventorNames": ["Anderson; Evan K. Seattle", "Patel; Rina Mountain View"],
        }
    ]


def test_preload_loads_only_missing_documents(tmp_path: Path) -> None:
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    first = _document("alpha", "Alpha Patent")
    second = _document("beta", "Beta Patent")

    first_path = parsed_dir / "alpha.json"
    second_path = parsed_dir / "beta.json"
    first_path.write_text(first.model_dump_json(exclude_none=True), encoding="utf-8")
    second_path.write_text(second.model_dump_json(exclude_none=True), encoding="utf-8")

    store = DocumentStore()
    store.load_from_parsed_dir(parsed_dir)

    preloaded = store.preload(["alpha", "beta", "missing"])

    assert preloaded == 2
    assert store.stats()["lazyLoads"] == 2
    assert store.stats()["preloadRequests"] == 1
    assert store.stats()["preloadedDocuments"] == 2

    second_preload = store.preload(["alpha", "beta"])

    assert second_preload == 0
    assert store.stats()["preloadedDocuments"] == 2


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