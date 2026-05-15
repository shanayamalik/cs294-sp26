from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .dsl_parser import parse_dsl
from .models import ParseDocumentRequest, PreloadDocumentsRequest, QueryRequest
from .parser import parse_patent_text
from .query_engine import execute_query_across_documents
from .source_loader import load_source_text
from .store import DocumentStore
from .synonym_sets import synonym_seed_summaries

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BACKEND_ROOT / "data" / "raw"
PARSED_DATA_DIR = BACKEND_ROOT / "data" / "parsed"

store = DocumentStore()
app = FastAPI(title="Patent Query Prototype API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    store.load_from_parsed_dir(PARSED_DATA_DIR)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/documents")
def documents() -> dict[str, list[dict[str, Any]]]:
    return {"documents": store.list()}


@app.post("/documents/preload")
def preload_documents(payload: PreloadDocumentsRequest) -> dict[str, Any]:
    return {
        "requestedDocuments": len(payload.documentIds),
        "preloadedDocuments": store.preload(payload.documentIds),
        "stats": store.stats(),
    }


@app.get("/debug/store-stats")
def store_stats() -> dict[str, int | float]:
    return store.stats()


@app.get("/query/synonym-sets")
def query_synonym_sets() -> dict[str, list[dict[str, list[str] | str]]]:
    return {"synonymSets": synonym_seed_summaries()}


@app.post("/documents/parse")
def parse_document(payload: ParseDocumentRequest) -> dict[str, str]:
    source_path = RAW_DATA_DIR / payload.fileName
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Raw file not found: {payload.fileName}")

    try:
        raw_text = load_source_text(source_path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    doc_id = _filename_to_id(payload.fileName)
    document = parse_patent_text(doc_id=doc_id, source_file=payload.fileName, raw_text=raw_text)

    store.upsert(document)
    out_path = store.write_document(PARSED_DATA_DIR, document)

    return {"documentId": doc_id, "outputPath": str(out_path)}


@app.post("/query")
def run_query(payload: QueryRequest):
    documents = []
    missing_document_ids = []
    seen_document_ids = set()

    for document_id in payload.documentIds:
        if document_id in seen_document_ids:
            continue

        seen_document_ids.add(document_id)
        document = store.get(document_id)
        if document is None:
            missing_document_ids.append(document_id)
        else:
            documents.append(document)

    if missing_document_ids:
        raise HTTPException(status_code=404, detail=f"Document not found: {', '.join(missing_document_ids)}")

    try:
        query = parse_dsl(payload.queryText)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    result = execute_query_across_documents(documents, query)
    return {"query": query.model_dump(), "result": result.model_dump()}


def _filename_to_id(file_name: str) -> str:
    lowered = Path(file_name).stem.lower()
    normalized = "".join(ch if ch.isalnum() else "-" for ch in lowered)
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-")
