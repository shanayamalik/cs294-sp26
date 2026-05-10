# CS 294-184 Final Project Part 2: Programmatic Document Analysis for Patent Examination

We design a programming-oriented document analysis environment where patent documents are treated as structured, queryable data. Instead of manual keyword search and scanning, examiners define reusable document-level queries over structure (sections, passages, metadata) to systematically retrieve and analyze relevant evidence.

## Repository Layout

- `backend/` FastAPI + Python API, parser pipeline, query engine, DSL parser
- `frontend/` React + Vite UI for running queries and viewing results
- `docs/` MVP scope, architecture, and query examples

## Current MVP

- Document model: `Document -> Section -> Passage`
- Parser for constrained raw patent inputs (`.txt` and text-extractable `.pdf`)
- Internal query model with filters:
  - `section == TYPE`
  - `meta.KEY == VALUE` (optional)
  - `meta.KEY < VALUE`, `<=`, `>`, `>=` for comparable metadata such as filing dates
  - `meta.KEY ~ VALUE` / `^ VALUE` for substring and prefix matching on string metadata such as assignee or inventor names
  - `cpc == CODE` (optional)
  - `contains("phrase")`
  - `paragraph == NNNN` (optional pinpoint drill-down)
- Boolean logic: `AND`, `OR`, `NOT`, parentheses with proper precedence
- Lightweight textual DSL:
  - `section:SUMMARY AND contains:"normalizer task queue"`
  - `section:CLAIMS AND paragraph:0042`
  - `meta.filingDate:<2018-03-15 AND section:SPECIFICATION`
  - `meta.assignee.name:~"Google"`
  - `contains:"server" OR contains:"network"`
  - `NOT section:OTHER`
- Query execution with provenance metadata, grouped by matched document
- Thin UI to run queries and inspect passage context
- Result cards show per-match provenance, including document id, section, passage index, and anchor badges when available (`paragraphId`, `claimNo`)
- Live query refresh with a 600ms debounce for iterative query refinement

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
section:SUMMARY AND contains:"normalizer task queue"
```

## What's Been Done (shanaya branch)

- `paragraph:NNNN` filter implemented and tested against USPTO PDF patents
- `OR` and `NOT` boolean operators fully supported
- Multi-document querying with per-result document provenance
- Result cards now display paragraph / claim anchors (`¶[N]`, `Claim N`) when available
- Filing-date comparison filters now supported for comparable metadata fields such as `meta.filingDate:<2018-03-15`
- Metadata exploration supports substring and prefix matching such as `meta.assignee.name:~"Google"`
- PDF patent parsing via `pypdf` (5 USPTO PDFs in `backend/data/raw/`)
- `npm run dev:backend` fixed to use venv python
- Frontend build config cleaned up so TypeScript no longer emits stale `.js` / `.d.ts` files into `frontend/src`

## Next Steps

- Need-finding-motivated filters (especially filing-date comparison and richer metadata predicates)
- Claim-mapping workflow support beyond retrieval (copy/export citations, structured claim charting)
- Query authoring aids (cheat sheet, examples, saved query snippets)
- Pre-loading / lazy loading for larger document sets
- USPTO API integration
