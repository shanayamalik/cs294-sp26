# Programmatic Patent Query DSL

This repository centers on a domain-specific language for structured prior-art search over patent documents. The DSL treats patents as structured, queryable data rather than opaque full-text blobs, allowing users to express searches over section type, passage content, metadata, and citation-relevant anchors.

The surrounding system is a prototype implementation of that language: a FastAPI backend, a normalized patent document model, and a React frontend for running queries, inspecting provenance-rich results, and carrying selected evidence into a lightweight claim-chart workflow.

## Repository Layout

- `backend/`: parser pipeline, normalized document model, DSL parser, query engine, FastAPI endpoints, and backend tests
- `frontend/`: React and Vite application for corpus management, querying, result inspection, and claim-chart editing
- `docs/`: project scope notes and example DSL queries

## Core Capabilities

- Structured patent model: `Document -> Section -> Passage`
- Parsing for raw `.txt` patents and text-extractable `.pdf` patents
- Passage-level query execution over structural, textual, and metadata predicates
- Boolean composition with `AND`, `OR`, `NOT`, and parentheses
- Filters for section, heading, phrase/regex containment, CPC, paragraph, claim, figure, and metadata
- Synonym expansion support via `synonym_of:"term"` and curated `termset:"name"`
- Provenance-rich results with section metadata, neighboring context, and passage anchors when available
- Claim-chart workflow with evidence carry-forward and export support
- Live query refinement with debounced frontend updates

## Quick Start

1. Install JavaScript dependencies from the repository root.

```bash
npm install
```

2. Create and activate the backend virtual environment, then install Python dependencies.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

3. Start the backend.

```bash
npm run dev:backend
```

4. In a separate terminal, start the frontend.

```bash
npm run dev:frontend
```

5. Open the URL printed by Vite, typically `http://localhost:5173`.

## Working With Patent Data

- Add raw source files to `backend/data/raw/`.
- Run `npm run parse:raw` to regenerate parsed patent JSON.
- Parsed outputs in `backend/data/parsed/` are derived artifacts and may need to be regenerated after pulling new raw data.

## Common Commands

- `npm run dev:backend`: start the FastAPI backend with reload
- `npm run dev:frontend`: start the Vite frontend
- `npm run test:backend`: run backend tests with pytest
- `npm run parse:raw`: parse raw patent sources into normalized JSON

## Notes

- PDF support currently depends on text extraction through `pypdf`; image-only PDFs require OCR before ingestion.
- Example DSL queries are available in [docs/example-queries.md](docs/example-queries.md).
- Current MVP scope notes are available in [docs/mvp-scope.md](docs/mvp-scope.md).
