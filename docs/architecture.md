# Architecture Sketch (MVP)

## Core Abstractions

- `Document`
  - `metadata`
  - `sections[]`
- `Section`
  - `type`
  - `title`
  - `passages[]`
- `Passage`
  - `id`
  - `text`
  - `index`
  - `sectionType`
  - `startOffset`
  - `endOffset`

## Pipeline

1. Raw patent text is loaded from `backend/data/raw/`.
   Supported sources: `.txt` and text-extractable `.pdf`.
2. Parser detects section headings and splits section bodies into paragraph-level passages.
3. Structured JSON is written to `backend/data/parsed/`.
4. Query DSL text is parsed into an internal query object.
5. Execution engine applies filters over passages and returns matched results with context and provenance.
6. Frontend calls backend and renders matches grouped with section metadata.

## Implementation Notes

- Backend API is implemented in Python with FastAPI.
- Frontend is a thin React client that calls `/documents`, `/documents/parse`, and `/query`.

## Design Constraints

- Input format is intentionally constrained for a demoable prototype.
- Query language is intentionally small (section filter + contains + AND).
- Section normalization collapses many headings into MVP types to keep semantics stable.
