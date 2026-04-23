# CS 294-184 Final Project Part 2: Programmatic Document Analysis for Patent Examination

We design a programming-oriented document analysis environment where patent documents are treated as structured, queryable data. Instead of manual keyword search and scanning, examiners define reusable queries over document structure (sections, passages, metadata) to systematically retrieve and analyze relevant evidence.

## Repository Layout

- `backend/` FastAPI + Python API, parser pipeline, query engine, DSL parser
- `frontend/` React + Vite UI for running queries and viewing results
- `docs/` MVP scope, architecture, and query examples

## Current MVP

- Document model: `Document -> Section -> Passage`
- Parser for constrained raw patent inputs (`.txt` and text-extractable `.pdf`)
- Internal query model with filters:
  - `section == TYPE`
  - `contains("phrase")`
  - `AND`
- Lightweight textual DSL:
  - `section:SPECIFICATION AND contains:"signal processing"`
- Query execution with provenance metadata
- Thin UI to run queries and inspect passage context

## Quick Start

1. Install frontend dependencies:

```bash
npm install
```

2. Set up backend Python environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

3. Start backend:

```bash
npm run dev:backend
```

4. In another terminal, start frontend:

```bash
npm run dev:frontend
```

5. Open the frontend URL printed by Vite (usually `http://localhost:5173`).

## Backend Scripts

- `npm run dev:backend` - start FastAPI with auto-reload on port `4000`
- `npm run test:backend` - run backend unit tests with pytest
- `npm run parse:raw` - parse all supported files in `backend/data/raw/` (`.txt`, `.pdf`) into JSON

## PDF Notes

- PDF parsing currently uses text extraction (`pypdf`), not OCR.
- If a PDF is image-only/scanned, run OCR first before ingestion.

## Example Query DSL

```text
section:SPECIFICATION AND contains:"signal processing"
```

## Current Goals

1. Parse one additional patent into structured JSON.
2. Add `OR` support to the internal query model.
3. Add query reuse across multiple documents.
4. Add one evaluator-facing demo scenario tied to need-finding.
