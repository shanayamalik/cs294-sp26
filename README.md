# CS 294-184 Final Project Part 2: Programmatic Document Analysis for Patent Examination

We design a programming-oriented document analysis environment where patent documents are treated as structured, queryable data. Instead of manual keyword search and scanning, examiners define reusable document-level queries over structure (sections, passages, metadata) to systematically retrieve and analyze relevant evidence.

## Overview

This prototype combines a FastAPI backend, a lightweight patent-query DSL, and a React frontend for passage-level retrieval over parsed patent documents. The current system supports multi-document querying, passage provenance, metadata-aware filtering, and an isolated claim-chart demo workflow for collecting retrieved evidence.

## Repository Layout

- `backend/` FastAPI + Python API, parser pipeline, query engine, DSL parser
- `frontend/` React + Vite UI for running queries and viewing results
- `docs/` MVP scope, architecture, and query examples

## Current Features

- Document model: `Document -> Section -> Passage`
- Parser for constrained raw patent inputs (`.txt` and text-extractable `.pdf`)
- Boolean logic: `AND`, `OR`, `NOT`, parentheses with proper precedence
- Query filters for section, phrase/regex containment, CPC, paragraph anchor, and metadata
- Metadata support for:
  - exact match
  - date and numeric comparison (`<`, `<=`, `>`, `>=`)
  - substring and prefix match (`~`, `^`)
  - convenience aliases such as `meta.pubDate`, `meta.published`, `meta.appNo`, `meta.filing`, `meta.appDate`, `meta.assigneeName`, and `meta.inventorName`
  - derived helper fields such as `meta.priorityDate`, `meta.effectiveDate`, and `meta.admissibilityDate`
- Query execution with provenance metadata, grouped by matched document
- Frontend document picker for multi-document search
- Result cards with document provenance, section metadata, neighboring context, and anchor badges when available (`paragraphId`, `claimNo`)
- `Copy citation` and `Add to chart` actions on result cards
- Separate `#claim-chart-demo` page for grouped evidence collection, TSV export, and DOCX claim-chart export
- Live query refresh with a 600ms debounce for iterative query refinement

## Example Queries

```text
section:SUMMARY AND contains:"normalizer task queue"
section:CLAIMS AND paragraph:0042
meta.filingDate:<2018-03-15 AND section:SPECIFICATION
meta.pubDate:>=2019-01-01
meta.assigneeName:~"Google"
meta.inventorName:^"Anderson" AND contains:"virtual machine"
meta.priorityDate:<2011-07-01
meta.admissibilityDate:<2011-07-01
contains:"server" OR contains:"network"
contains.regex:"virtual\s+machine|hypervisor"
NOT section:OTHER
```

More examples are in [docs/example-queries.md](docs/example-queries.md).

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

## Working With New Patents

- Add new source patents to `backend/data/raw/` as text-extractable `.pdf` files or `.txt` files.
- Regenerate the parsed corpus with `npm run parse:raw`.
- Parsed `backend/data/parsed/*.generated.json` files are treated as derived artifacts and are gitignored, so teammates should rerun `npm run parse:raw` after pulling new raw patent files.

## Common Commands

- `npm run dev:backend` - start FastAPI with auto-reload on port `4000`
- `npm run dev:frontend` - start the Vite frontend
- `npm run test:backend` - run backend unit tests with pytest
- `npm run parse:raw` - parse supported files in `backend/data/raw/` into JSON

## PDF Notes

- PDF parsing currently uses text extraction (`pypdf`), not OCR.
- If a PDF is image-only/scanned, run OCR first before ingestion.

## Documentation

- [docs/example-queries.md](docs/example-queries.md) - query examples
- [docs/mvp-scope.md](docs/mvp-scope.md) - current scope and implemented MVP state
- [docs/architecture.md](docs/architecture.md) - architecture notes
