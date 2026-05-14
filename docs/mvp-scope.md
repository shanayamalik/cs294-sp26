# MVP Scope

## Current State (Updated Post Demo)

- Constrained raw patent input formats (`.txt` and text-extractable `.pdf`), including USPTO-style patent PDFs
- Fixed hierarchy: `Document -> Section -> Passage`
- Document-level metadata extraction:
  - core metadata: `id`, `title`, `sourceFile`, `ingestedAt`
  - patent metadata: `documentId`, dates, `applicationNo`, inventors, assignee, CPC, domestic priority, US class
- Passage splitting by:
  - blank-line paragraphs
  - patent numbered paragraphs
  - claims
- Passage annotations:
  - passage ids and offsets
  - optional anchors (`paragraphId`, `claimNo`) when available
  - optional `figureRefs`
- Query filters:
  - `section:TYPE`, including finer-grained section filters such as `BACKGROUND`, `SUMMARY`, and `DESCRIPTION` while preserving `SPECIFICATION` as a broader umbrella filter
  - `contains:"phrase"` for plain text and `contains.regex:"pattern"` for regex patterns
  - `meta.KEY:"value"`
  - `meta.KEY:<value`, `<=value`, `>value`, `>=value` for comparable metadata fields such as filing dates
  - `meta.KEY:~value`, `^value` for substring and prefix matching on string metadata
  - nested metadata paths such as `meta.assignee.name:"value"`
  - `cpc:"code"`
  - `paragraph:NNNN` (pinpoint filter by numbered paragraph anchor)
- Query boolean logic:
  - `AND`
  - `OR`
  - `NOT`
  - parentheses, precedence, nested expressions
- Result output with:
  - matches across one or more selected documents
  - document id on each match
  - matched passage text
  - section metadata
  - optional anchors (`paragraphId`, `claimNo`) when available
  - neighboring context
  - match reasons
- Frontend document picker supports searching across multiple documents
- Frontend result cards show which document each hit came from
- Frontend result cards show paragraph / claim anchor badges when available
- Frontend result cards support `Copy citation` for lightweight claim-mapping handoff
- Frontend result cards support `Add to chart`, which sends live results into the separate claim-chart demo workspace
- Frontend uses 600ms debounced live refresh so result sets update during query refinement after the user begins interacting
- Separate `#claim-chart-demo` page provides an isolated claim-chart workspace with grouped claim elements, editable evidence/analysis fields, TSV export, and examiner-style DOCX export
- Claim-chart demo persists saved rows in the browser so the search page and chart page stay connected without merging the workflows
- Backend document store now indexes lightweight metadata separately from full document payloads and lazy-loads full documents on demand
- Parsed document metadata can now be preprocessed into sidecar metadata files so startup indexing avoids reading full passage bodies
- Frontend can opportunistically preload currently selected documents after user interaction instead of waiting for the first query to hydrate them one by one
- Demo corpus includes parsed sample patent data and multiple USPTO patent PDFs
- Supported demo queries are captured in [example-queries.md](example-queries.md)

## Goal Features

- More Query filters:
  - ~~`paragraph:NNNN` (optional pinpoint filter, not primary retrieval)~~ **done** 
  - ~~add finer-grained section filters so users can distinguish `BACKGROUND`, `SUMMARY`, and detailed-description style sections instead of only the broader `SPECIFICATION` bucket~~ **done**
  - remaining action items:
    - consider a heading-text filter such as `heading:` / `sectionTitle:` as an escape hatch when canonical section typing is too coarse or parser normalization is imperfect
    - consider exposing already-extracted structural fields such as `claimNo` and `figureRefs` as queryable filters if we want more patent-specific retrieval beyond `paragraph:` and `cpc:`
- More *Unique* Query filters specific to examiner workflows that we can extract from need finding
  - recommended focus:
    - add reusable synonym support rather than relying only on manual `OR` clauses, since Need 1 is about managing synonym sets rather than only expressing them
    - decide whether synonym support should live in the DSL itself, in the UI as query-building assistance, or in a hybrid model with saved term sets expanded into plain DSL queries
- ~~Filing-date comparison / admissibility filters (for example `meta.filingDate:<2018-03-15`)~~ **done**
- Better metadata operators for inventor / assignee / date exploration
  - ~~substring / prefix matching, direct inventor / assignee name aliases, date convenience aliases, and derived priority / effective / admissibility date helpers~~ **done**
  - remaining action items:
    - add richer inventor / assignee facets beyond direct name lookup
    - decide whether any additional metadata fields should become first-class aliases instead of nested-only access
    - document the current legal limits of the helper-based `priorityDate` / `effectiveDate` / `admissibilityDate` model before extending it
- Claim-mapping support built on top of retrieved passages
  - ~~copy citation button~~ **done**
  - ~~separate claim-chart demo page~~ **done**
  - ~~stronger chart structure, better claim-element editing, grouped multi-evidence claim elements, TSV export, and examiner-style DOCX export~~ **done**
  - remaining action items:
    - add faster navigation between search hits and their grouped chart entries
    - support row or group reordering inside the claim-chart workspace
    - support bulk actions such as removing or clearing multiple evidence rows at once
    - decide whether chart groups need richer per-group notes or status fields beyond claim text, element label, and analysis
    - refine DOCX output layout if we want a closer match to a specific examiner-style template
    - decide whether export should include optional header fields such as patent number, claim set, analyst, or generation metadata
- shanaya (me) wouldlike to do UI polish / visual redesign
  - I will do these on a separate branch so u cans see if u like it and find it aesthetic before we merge
- Pre-loading and lazy loading of documents to improve performance, speed and memory usage
  - ~~measure the current baseline for startup loading and document hydration~~ **done**
  - ~~move startup loading to lightweight metadata indexing instead of eager full-document hydration~~ **done**
  - ~~separate lightweight metadata loading from full passage-body loading so document discovery stays fast~~ **done**
  - ~~avoid broad initial hydration from default UI state on first page load~~ **done**
  - ~~add opportunistic preloading for the currently selected documents after user interaction~~ **done**
  - ~~add backend instrumentation so lazy loads, cache hits, and preload requests can be observed directly~~ **done**
  - remaining action items:
    - benchmark this behavior against a meaningfully larger corpus instead of only the current demo set
    - decide whether preload signals should expand beyond explicit selection to recent queries or likely-next documents
    - design a cache/eviction policy so preloading remains helpful on larger document groups
    - decide whether any additional preprocessing should happen ahead of time for thousands of pre-selected documents beyond metadata sidecars
    - define acceptance thresholds for startup time, first-query latency, and memory usage on larger corpora
- USPTO search integration
  - Chrome/Browser extension?
  - API integration with [USPTO API](https://data.uspto.gov/apis/getting-started)


### Recommended Next Implementation Order

- Highest priority / strongest writeup alignment:
  - add real synonym-management support (saved term sets, assisted expansion, or hybrid UI + DSL support) so Need 1 is addressed as workflow support rather than only manual `OR` composition
  - add jump/navigation links between search results and grouped claim-chart entries so the current search-to-chart handoff becomes a true workflow rather than a one-way transfer
- Medium priority / strong workflow payoff:
  - add row or group reordering in the claim-chart workspace so grouped evidence can be organized into a reviewer-friendly order
  - add bulk evidence actions such as remove-selected / clear-selected so chart cleanup does not stay fully manual as saved evidence grows
  - expose more patent-specific structure in the DSL, especially `claimNo` and possibly `figureRefs`, if we want a more distinctive examiner-focused query story
- Lower priority / important for polish or validation:
  - add richer inventor / assignee facets and decide which metadata fields deserve first-class aliases instead of only nested access
  - document the legal limits of the helper-based date fields before extending them further, so the tool stays honest about what is heuristic versus legally definitive
  - benchmark lazy-load / preload behavior on a larger corpus and define concrete acceptance targets for startup latency, first-query latency, and memory use
- Likely defer unless time remains:
  - smarter preload prediction beyond explicit document selection
  - USPTO integration surfaces such as an extension or API-backed search bridge
  - semantic ranking, embeddings, or cross-document joins, since these are less central to the current writeup than the workflow gaps above


### Additional Thoughts

- side-by-side interface between query dsl and hits in initial search query documents (set of documents our dsl will search over)
  - should support very fast indexing of all documents, very quickly adapting the search with fast refreshes (possibly 
  interesting work in determining a way to develop fast indexing of documents?)
  - ~~ideally should nearly match the speed of autocorrect systems (nothing happens as you type, but once you stop for 
  a second or less, then updated results should appear)~~ **done** — 600ms debounced live refresh implemented 

- Most importantly, *include interesting features unique from current USPTO search query* capabilities
  - some feature overlaps can be fine due to enhancements from our interface vs USPTO search interface (passage-level 
  vs document-level search) and difference in part of workflow (find relevant potentially relevant docs -> determine 
  relevance of docs and find specific pieces of evidence)

  - built-in synonyms with `synonym_of:"term"` *justification/need-finding relation*
    - even though you would ideally determine synonyms to find relevant documents on your document-level initial search,
    this still provides a proof-of-concept for assistance when patent examiners are lacking comprehensive vocab coverage
    in their searches
    - to determine synonyms, can do a couple options:
      - search on initial documents from intial `"term"`, then take found synonyms in those docs/passages and repeat 
      search
      - use llm to give synonyms (can or can not be integrated in actual DSL but in webapp instead?)
        - ideally it would be integrated tbh
      - use a general lexical database like WordNet (likely too general and weak for actual patent examiner worflows)


### Stretchy Goals

- Semantic ranking models
- Cross-document joins
- Embedding-based retrieval




## Demo Goals (Done)

### Frontend

- Support search across multiple documents (currently restrained to single document at a time)
  - Instead of selecting the document to search for in the dropdown, we should either be selected the group of 
  documents to search from, or remove the dropdown entirely and incorporate the documents select in the search 
  query as a `SELECT documents` selector
  - The search results section should also support this multi-document searching by:
    1. Determining if all results from all queried documents show up in the results section in the first place
    2. Add a label in each result showing which document the result came from (currently only shows section 
    and passage index)

### Backend

- Determine a topic/patent we want to use as our base for the demo queries and to collect documents for
  - Save and show off a few of the most interesting demo queries
- Support parsing and querying of actual format of documents
  - Currently does support both `.txt` and `.pdf` files, but indeterminant whether the actual document format from 
  USPTO search is support and can be properly queried
- Determine current scope of implemented features and features we should implement
  - A few of the most interesting features from [goal features](#goal-features) i.e.:
    - More patent-specific metadata extraction and related query filters
    - `OR` and `NOT` (not could be optional for now)
    - Support `cpc:"code"`
