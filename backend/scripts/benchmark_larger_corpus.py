from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from time import perf_counter

from app.dsl_parser import parse_dsl
from app.models import Document
from app.query_engine import execute_query_across_documents
from app.store import DocumentStore

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PARSED_DIR = BACKEND_ROOT / "data" / "parsed"
DEFAULT_QUERY = 'section:SPECIFICATION AND contains:"system"'
DEFAULT_TARGET_DOCUMENTS = 30


def load_unique_documents(parsed_dir: Path) -> list[Document]:
    documents_by_id: dict[str, Document] = {}

    for file_path in sorted(parsed_dir.glob("*.json")):
        if file_path.name.endswith(".metadata.json"):
            continue

        document = Document.model_validate_json(file_path.read_text(encoding="utf-8"))
        documents_by_id.setdefault(document.metadata.id, document)

    return list(documents_by_id.values())


def clone_document(template: Document, clone_number: int) -> Document:
    clone = template.model_copy(deep=True)
    suffix = f"-clone-{clone_number:03d}"
    source_path = Path(clone.metadata.sourceFile)

    clone.metadata.id = f"{clone.metadata.id}{suffix}"
    clone.metadata.title = f"{clone.metadata.title} (Clone {clone_number})"
    clone.metadata.sourceFile = f"{source_path.stem}{suffix}{source_path.suffix}"

    if clone.metadata.documentId:
        clone.metadata.documentId = f"{clone.metadata.documentId}{suffix}"

    return clone


def write_synthetic_corpus(base_documents: list[Document], target_documents: int, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_ids: list[str] = []

    for index in range(target_documents):
        template = base_documents[index % len(base_documents)]
        clone = clone_document(template, index + 1)
        payload_path = output_dir / f"{clone.metadata.id}.generated.json"
        metadata_path = output_dir / f"{clone.metadata.id}.generated.metadata.json"

        payload_path.write_text(clone.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
        metadata_path.write_text(clone.metadata.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
        written_ids.append(clone.metadata.id)

    return written_ids


def benchmark_startup(parsed_dir: Path) -> dict[str, int | float]:
    store = DocumentStore()
    started = perf_counter()
    store.load_from_parsed_dir(parsed_dir)
    elapsed = perf_counter() - started

    return {
        "startupIndexSecondsMeasured": round(elapsed, 6),
        **store.stats(),
    }


def benchmark_preload(parsed_dir: Path) -> dict[str, int | float]:
    store = DocumentStore()
    store.load_from_parsed_dir(parsed_dir)
    document_ids = [document["id"] for document in store.list()]

    started = perf_counter()
    preloaded_documents = store.preload(document_ids)
    elapsed = perf_counter() - started

    return {
        "requestedDocuments": len(document_ids),
        "preloadedDocumentsMeasured": preloaded_documents,
        "preloadSecondsMeasured": round(elapsed, 6),
        **store.stats(),
    }


def benchmark_query(parsed_dir: Path, query_text: str) -> dict[str, int | float | str]:
    query = parse_dsl(query_text)
    store = DocumentStore()
    store.load_from_parsed_dir(parsed_dir)
    document_ids = [document["id"] for document in store.list()]

    started = perf_counter()
    documents = [document for document_id in document_ids if (document := store.get(document_id)) is not None]
    cold_result = execute_query_across_documents(documents, query)
    cold_elapsed = perf_counter() - started
    cold_stats = store.stats()

    started = perf_counter()
    warm_result = execute_query_across_documents(documents, query)
    warm_elapsed = perf_counter() - started
    warm_stats = store.stats()

    return {
        "queryText": query_text,
        "queriedDocuments": len(documents),
        "coldQuerySecondsMeasured": round(cold_elapsed, 6),
        "warmQuerySecondsMeasured": round(warm_elapsed, 6),
        "coldQueryMatches": cold_result.totalMatches,
        "warmQueryMatches": warm_result.totalMatches,
        "coldLazyLoads": cold_stats["lazyLoads"],
        "coldCacheHits": cold_stats["cacheHits"],
        "coldLazyLoadSeconds": round(float(cold_stats["lazyLoadSeconds"]), 6),
        "warmCacheHits": warm_stats["cacheHits"],
        "warmLazyLoads": warm_stats["lazyLoads"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark startup, preload, and query timings on a synthetic larger corpus.")
    parser.add_argument("--target-documents", type=int, default=DEFAULT_TARGET_DOCUMENTS, help="Synthetic corpus size to benchmark.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Query text to run for the cold/warm query benchmark.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_documents = load_unique_documents(PARSED_DIR)
    if not base_documents:
        raise SystemExit(f"No parsed documents found in {PARSED_DIR}")

    with tempfile.TemporaryDirectory(prefix="synthetic-patent-corpus-") as temp_dir:
        synthetic_dir = Path(temp_dir)
        written_ids = write_synthetic_corpus(base_documents, args.target_documents, synthetic_dir)

        summary = {
            "baseDocuments": len(base_documents),
            "syntheticDocuments": len(written_ids),
            "startup": benchmark_startup(synthetic_dir),
            "preload": benchmark_preload(synthetic_dir),
            "query": benchmark_query(synthetic_dir, args.query),
        }

        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()