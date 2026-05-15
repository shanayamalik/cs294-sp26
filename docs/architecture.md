# Architecture Sketch

## System Overview

The prototype has two main layers:

1. A Python/FastAPI backend that parses patents into structured JSON and executes a lightweight DSL over document metadata and passage content.
2. A React/Vite frontend that supports multi-document querying, result inspection, and a separate client-side claim-chart workspace.

The current architecture is still document-first, but the frontend now includes a workflow layer for collecting retrieved evidence into grouped claim elements and exporting that chart to TSV or DOCX.

## Core Data Model

- `Document`
  - `metadata`
  - `sections[]`
- `DocumentMetadata`
  - core fields: `id`, `title`, `sourceFile`, `ingestedAt`
  - patent fields: `documentId`, `publicationDate`, `applicationNo`, `filingDate`, `applicationFilingDate`, `inventors`, `assignee`, `cpc`, `domesticPriority`, `usClassCurrent`
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
  - optional anchors: `paragraphId`, `claimNo`, `figureRefs`

The backend stores parsed patents as JSON in `backend/data/parsed/` and loads them into an in-memory document store on API startup.

## Backend Flow

1. Raw patent sources are read from `backend/data/raw/`.
   Supported inputs are `.txt` and text-extractable `.pdf`.
2. The parser extracts metadata, detects section headings, and splits sections into passage-level units.
3. Passage-level anchors such as numbered paragraphs and claims are attached when available.
4. Parsed documents are written to `backend/data/parsed/` and later loaded into the FastAPI store.
5. The query API accepts a document set plus DSL text and returns matching passages with provenance.

## Query Layer

The DSL is parsed into an internal expression tree with support for:

- section filters
- phrase filters
- CPC filters
- paragraph anchor filters
- metadata filters with exact match, comparison, substring, and prefix operators
- Boolean composition with `AND`, `OR`, `NOT`, and parentheses

The query engine evaluates expressions over passages across the selected document set. Matches carry document provenance, section information, neighboring context, reasons, and optional anchors.

Metadata access now includes:

- nested metadata paths such as `meta.assignee.name`
- convenience aliases such as `meta.pubDate`, `meta.appNo`, `meta.assigneeName`, and `meta.inventorName`
- derived helper fields such as `meta.priorityDate`, `meta.effectiveDate`, and `meta.admissibilityDate`

## Frontend Flow

The frontend has two distinct UI surfaces:

1. Main search page
   - loads available documents from `/documents`
   - runs live or submitted DSL queries against `/query`
   - renders result cards with provenance, context, citation copying, and an `Add to chart` action
2. Claim-chart demo page (`#claim-chart-demo`)
   - reads saved evidence rows from browser storage
   - groups evidence rows by claim and element label
   - lets the user edit claim text, element labels, claim-element text, and per-evidence analysis
   - exports grouped claim-chart content as TSV or DOCX

The chart workflow is intentionally isolated from the main search screen. The bridge between them is client-side storage rather than a backend workflow API, which keeps experimentation local and low-risk.

## Claim-Chart Workspace Model

The chart workspace stores flat evidence rows in local storage, but renders them as grouped claim elements.

Each stored row includes:

- claim
- element label
- citation
- excerpt
- analysis notes

Rows that share the same claim and element label are grouped together under one claim element in the UI. This supports multiple evidence rows under a single claim limitation while keeping the storage model simple.

## Export Path

There are currently two client-side export modes:

- TSV export for quick spreadsheet-style transfer
- DOCX export for a more examiner-style chart document

The DOCX export is generated in the frontend using a document-generation library and reflects the grouped chart structure rather than raw ungrouped evidence rows.

## Implementation Notes

- Backend: FastAPI + Python
- Frontend: React + Vite + TypeScript
- Claim-chart state: browser local storage
- Chart document export: client-side DOCX generation
