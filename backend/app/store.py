from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from .models import Document, DocumentMetadata

DEMO_TITLE_OVERRIDES = {
    "us-10324754-b2": "Managing virtual machine patterns",
    "us-10747562-b2": "Nested hypervisor to run virtual machines on public clouds",
    "us-10977063-b2": "Elastic compute fabric using virtual machine templates",
    "us-8565118-b2": "Methods and apparatus for distributed dynamic network provisioning",
    "us-8874749-b1": "Network fragmentation and virtual machine migration in a scalable cloud computing environment",
    "us-9176767-b2": "Network interface card device pass-through with multiple nested hypervisors",
    "us-9229755-b2": "User datagram protocol (UDP) packet migration in a virtual machine (VM) migration",
    "us-9733973-b2": "Automatically determining sensor location in a virtualized computing environment",
    "us-9858095-b2": "Dynamic virtual machine resizing in a cloud computing infrastructure",
}


class DocumentStore:
    def __init__(self) -> None:
        self._by_id: dict[str, Document] = {}
        self._metadata_by_id: dict[str, DocumentMetadata] = {}
        self._parsed_path_by_id: dict[str, Path] = {}
        self._stats = {
            "indexedDocuments": 0,
            "cachedDocuments": 0,
            "cacheHits": 0,
            "lazyLoads": 0,
            "preloadRequests": 0,
            "preloadedDocuments": 0,
            "startupIndexSeconds": 0.0,
            "lazyLoadSeconds": 0.0,
        }

    def upsert(self, document: Document) -> None:
        self._by_id[document.metadata.id] = document
        self._metadata_by_id[document.metadata.id] = document.metadata
        self._stats["cachedDocuments"] = len(self._by_id)
        self._stats["indexedDocuments"] = len(self._metadata_by_id)

    def get(self, document_id: str) -> Document | None:
        document = self._by_id.get(document_id)
        if document is not None:
            self._stats["cacheHits"] += 1
            return document

        parsed_path = self._parsed_path_by_id.get(document_id)
        if parsed_path is None:
            return None

        start = perf_counter()
        raw = parsed_path.read_text(encoding="utf-8")
        document = Document.model_validate_json(raw)
        self._stats["lazyLoads"] += 1
        self._stats["lazyLoadSeconds"] += perf_counter() - start
        self.upsert(document)
        return document

    def list(self) -> list[dict[str, str | list[str] | None]]:
        documents = sorted(self._metadata_by_id.values(), key=lambda metadata: metadata.id)
        return [
            {
                "id": metadata.id,
                "title": DEMO_TITLE_OVERRIDES.get(metadata.id, metadata.title),
                "sourceFile": metadata.sourceFile,
                "ingestedAt": metadata.ingestedAt,
                "assigneeName": metadata.assignee.get("name") if metadata.assignee else None,
                "inventorNames": [
                    inventor.get("nameAndCity", "")
                    for inventor in (metadata.inventors or [])
                    if inventor.get("nameAndCity")
                ]
                or None,
            }
            for metadata in documents
        ]

    def load_from_parsed_dir(self, parsed_dir: Path) -> None:
        if not parsed_dir.exists():
            return

        start = perf_counter()
        for file_path in sorted(parsed_dir.glob("*.json")):
            if file_path.name.endswith(".metadata.json"):
                continue

            metadata_path = _metadata_sidecar_path(file_path)
            if metadata_path.exists():
                raw_metadata = metadata_path.read_text(encoding="utf-8")
                metadata = DocumentMetadata.model_validate_json(raw_metadata)
            else:
                raw = file_path.read_text(encoding="utf-8")
                payload = json.loads(raw)
                metadata = DocumentMetadata.model_validate(payload["metadata"])
                metadata_path.write_text(metadata.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")

            self._metadata_by_id[metadata.id] = metadata
            self._parsed_path_by_id[metadata.id] = file_path

        self._stats["indexedDocuments"] = len(self._metadata_by_id)
        self._stats["startupIndexSeconds"] = perf_counter() - start

    def write_document(self, parsed_dir: Path, document: Document) -> Path:
        parsed_dir.mkdir(parents=True, exist_ok=True)
        out_path = parsed_dir / f"{document.metadata.id}.generated.json"
        out_path.write_text(document.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
        metadata_path = _metadata_sidecar_path(out_path)
        metadata_path.write_text(document.metadata.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
        self._parsed_path_by_id[document.metadata.id] = out_path
        return out_path

    def preload(self, document_ids: list[str]) -> int:
        self._stats["preloadRequests"] += 1
        preloaded = 0

        for document_id in document_ids:
            if document_id in self._by_id:
                continue

            if self.get(document_id) is not None:
                preloaded += 1

        self._stats["preloadedDocuments"] += preloaded
        return preloaded

    def stats(self) -> dict[str, int | float]:
        return dict(self._stats)


def _metadata_sidecar_path(document_path: Path) -> Path:
    return document_path.with_name(f"{document_path.stem}.metadata.json")
