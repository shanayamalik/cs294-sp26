# Architecture Sketch (MVP, Document-First)

## Core Abstractions

- `Document`
  - `id` (e.g., `US 20260113257 A1`)
  - `metadata` (`publicationDate`, `applicationNo`, `filingDate`, `inventors[]`, `cpc[]`)
  - `sections[]`
- `Section`
  - `type` (`TITLE`, `ABSTRACT`, `BACKGROUND`, `SUMMARY`, `SPECIFICATION`, `CLAIMS`, `OTHER`)
  - `title`
  - `passages[]`
- `Passage`
  - `id`
  - `text`
  - `index`
  - `sectionType`
  - `startOffset`
  - `endOffset`
  - `paragraphId` (optional anchor from bracket numbering like `0001`, `0047`)
  - `claimNo` (optional, mostly for passages in `CLAIMS`)
  - `figureRefs[]` (optional, e.g., `FIG. 1`, `FIG. 5A`)

## Pipeline

1. Raw patent text is loaded from `backend/data/raw/`.
   Supported sources: `.txt` and text-extractable `.pdf`.
2. Parser extracts document metadata (document id, dates, inventors, classifications).
3. Parser detects headings, normalizes them to `Section.type`, and splits section bodies into passage-level units.
4. Parser annotates optional anchors (`paragraphId`, `claimNo`, `figureRefs`) on passages when present.
5. Structured JSON is written to `backend/data/parsed/`.
6. Query DSL text is parsed into an internal query object.
7. Execution engine applies filters over passages across selected documents and returns matches grouped by document.
8. Frontend renders document-level results first, with passage-level evidence and optional anchors.

## Implementation Notes

- Backend API is implemented in Python with FastAPI.
- Frontend is a thin React client that calls `/documents`, `/documents/parse`, and `/query`.
