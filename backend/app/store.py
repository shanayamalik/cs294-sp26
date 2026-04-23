from __future__ import annotations

from pathlib import Path

from .models import Document


class DocumentStore:
    def __init__(self) -> None:
        self._by_id: dict[str, Document] = {}

    def upsert(self, document: Document) -> None:
        self._by_id[document.metadata.id] = document

    def get(self, document_id: str) -> Document | None:
        return self._by_id.get(document_id)

    def list(self) -> list[dict[str, str]]:
        documents = sorted(self._by_id.values(), key=lambda d: d.metadata.id)
        return [
            {
                "id": doc.metadata.id,
                "title": doc.metadata.title,
                "sourceFile": doc.metadata.sourceFile,
                "ingestedAt": doc.metadata.ingestedAt,
            }
            for doc in documents
        ]

    def load_from_parsed_dir(self, parsed_dir: Path) -> None:
        if not parsed_dir.exists():
            return

        for file_path in sorted(parsed_dir.glob("*.json")):
            raw = file_path.read_text(encoding="utf-8")
            document = Document.model_validate_json(raw)
            self.upsert(document)

    def write_document(self, parsed_dir: Path, document: Document) -> Path:
        parsed_dir.mkdir(parents=True, exist_ok=True)
        out_path = parsed_dir / f"{document.metadata.id}.generated.json"
        out_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")
        return out_path
