# MVP Scope

This document captures the current scope of the prototype as it exists in the
repository. It is intentionally narrower and more stable than a project TODO
list: the goal is to make clear what the MVP already supports, what constraints
still define the prototype, and which follow-up directions remain plausible.

## Current MVP

The current MVP is a patent-query prototype centered on a domain-specific
language for structured prior-art search. The system supports a lightweight
end-to-end workflow: load a scoped patent corpus, run passage-level DSL queries,
inspect provenance-rich results, and carry selected evidence into a simple
claim-chart workflow.

At a high level, the MVP includes:

- A normalized patent representation with a fixed `Document -> Section -> Passage` hierarchy
- Parsing for constrained raw patent inputs in `.txt` and text-extractable `.pdf` formats
- Metadata extraction for core patent fields used in filtering and corpus scoping
- A Boolean DSL for passage-level retrieval over structure, text, and metadata
- A React frontend for corpus selection, query authoring, and result inspection
- A lightweight claim-chart workflow for preserving and exporting selected evidence

## DSL Scope

The implemented DSL supports:

- Boolean composition with `AND`, `OR`, `NOT`, and parentheses
- Section filters such as `section:ABSTRACT`, `section:BACKGROUND`, `section:SUMMARY`, `section:DESCRIPTION`, `section:SPECIFICATION`, and `section:CLAIMS`
- Text predicates including `contains:"phrase"` and `contains.regex:"pattern"`
- Heading-oriented filters via `heading:"text"` and `sectionTitle:"text"`
- Metadata predicates of the form `meta.KEY:"value"`
- Comparable metadata filters using `<`, `<=`, `>`, and `>=` for fields such as dates
- String metadata operators using `~` for substring match and `^` for prefix match
- Nested metadata paths such as `meta.assignee.name:"value"`
- Patent-specific structural filters including `paragraph:NNNN`, `claim:NN`, `figure:"FIG. N"`, and `cpc:"code"`
- Synonym-oriented operators via `synonym_of:"term"` and `termset:"name"`

Representative queries are documented in [docs/example-queries.md](example-queries.md).

## Workflow Scope

The MVP currently supports the following workflow stages:

- Corpus scoping through document selection plus metadata-based narrowing
- Passage-level retrieval across one or more selected documents
- Result inspection with document identity, section metadata, neighboring context, and available anchors
- Lightweight handoff actions such as copying a citation trace or saving evidence into the claim-chart workflow
- Iterative refinement through debounced live query updates after user interaction begins

The claim-chart workflow is intentionally lightweight. It is designed to retain
selected evidence and support simple grouping, editing, and export, not to model
the full downstream structure of examiner reasoning.

## Data And System Constraints

The MVP is still constrained to the following:

- Patent ingestion is limited to `.txt` files and text-extractable `.pdf` files; image-only PDFs require OCR before ingestion
- Parsing depends on recoverable section structure and anchor information from the source material
- Legal admissibility is approximated through available metadata and helper fields, not a full priority-law model
- The current system is optimized for a small-to-moderate working corpus rather than production-scale patent retrieval
- Synonym support is explicit and inspectable, but still lightweight relative to expert patent vocabulary needs

These constraints are acceptable for the MVP because the prototype is meant to
demonstrate the DSL, the structured passage model, and the connected retrieval
workflow rather than to replace production patent-search infrastructure.

## Reasonable Next Steps

If the project is extended beyond the current MVP, the most natural next steps are:

- Better documentation of the legal limits of helper-based metadata fields such as `priorityDate`, `effectiveDate`, and `admissibilityDate`
- More deliberate synonym assistance, especially corpus-assisted suggestions that remain inspectable
- Incremental improvement to claim-chart structure, notes, and export formatting
- Clearer performance targets for startup latency, first-query latency, and memory use on larger corpora
- More principled scaling work for metadata indexing, caching, and preloading
