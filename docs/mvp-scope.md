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
  - `heading:"text"` / `sectionTitle:"text"` for case-insensitive section-heading substring matching
  - `synonym_of:"term"` / `termset:"name"` for Datamuse-backed synonym expansion into ordinary passage text matching, with optional `|max=N|topics="..."` modifiers on `synonym_of`
  - `claim:NN` for direct claim-number filtering
  - `figure:"FIG. N"` for filtering passages annotated with figure references
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
  - optional `figureRefs` when available
  - neighboring context
  - match reasons
- Frontend document picker supports searching across multiple documents
- Frontend document picker now exposes assignee and inventor facets so metadata can narrow the active document set before querying
- Frontend document picker now uses a simplified, title-first document list so uneven metadata extraction does not dominate corpus selection
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
- Demo corpus has been expanded beyond the original 6-document set to a larger working set and benchmarked on a synthetic 30-document corpus derived from the current parsed collection
- Supported demo queries are captured in [example-queries.md](example-queries.md)

## Goal Features

- More Query filters:
  - ~~`paragraph:NNNN` (optional pinpoint filter, not primary retrieval)~~ **done** 
  - ~~add finer-grained section filters so users can distinguish `BACKGROUND`, `SUMMARY`, and detailed-description style sections instead of only the broader `SPECIFICATION` bucket~~ **done**
  - ~~expose already-extracted structural fields such as `claimNo` and `figureRefs` as queryable filters~~ **done**
  - remaining action items:
    - ~~consider a heading-text filter such as `heading:` / `sectionTitle:` as an escape hatch when canonical section typing is too coarse or parser normalization is imperfect~~ **done**
- More *Unique* Query filters specific to examiner workflows that we can extract from need finding
  - recommended focus:
    - ~~add reusable synonym support rather than relying only on manual `OR` clauses, since Need 1 is about managing synonym sets rather than only expressing them~~ **done**
    - remaining action items:
      - ~~decide whether to keep synonym support as `synonym_of:"term"` only or also add a reusable `termset:` style syntax for named synonym groups~~ **done**
      - decide whether the next layer of synonym support should live in the UI as query-building assistance, in the DSL itself, or in a hybrid model
      - consider corpus-assisted synonym suggestions from the currently selected documents before adding any LLM-backed suggestion flow
- ~~Filing-date comparison / admissibility filters (for example `meta.filingDate:<2018-03-15`)~~ **done**
- Better metadata operators for inventor / assignee / date exploration
  - ~~substring / prefix matching, direct inventor / assignee name aliases, date convenience aliases, and derived priority / effective / admissibility date helpers~~ **done**
  - ~~add richer inventor / assignee facets beyond direct name lookup~~ **done**
  - remaining action items:
    - decide whether any additional metadata fields should become first-class aliases instead of nested-only access
    - document the current legal limits of the helper-based `priorityDate` / `effectiveDate` / `admissibilityDate` model before extending it
- Claim-mapping support built on top of retrieved passages
  - ~~copy citation button~~ **done**
  - ~~separate claim-chart demo page~~ **done**
  - ~~stronger chart structure, better claim-element editing, grouped multi-evidence claim elements, TSV export, and examiner-style DOCX export~~ **done**
  - ~~add faster navigation between search hits and their grouped chart entries~~ **done**
  - ~~support row or group reordering inside the claim-chart workspace~~ **done**
  - ~~support bulk actions such as removing or clearing multiple evidence rows at once~~ **done**
  - remaining action items:
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
    - ~~benchmark this behavior against a meaningfully larger corpus instead of only the current demo set~~ **done**
    - decide whether preload signals should expand beyond explicit selection to recent queries or likely-next documents
    - design a cache/eviction policy so preloading remains helpful on larger document groups
    - decide whether any additional preprocessing should happen ahead of time for thousands of pre-selected documents beyond metadata sidecars
    - define acceptance thresholds for startup time, first-query latency, and memory usage on larger corpora
- USPTO search integration
  - Chrome/Browser extension?
  - API integration with [USPTO API](https://data.uspto.gov/apis/getting-started)


### Recommended Next Implementation Order

- Highest priority / strongest writeup alignment:
  - decide which additional metadata fields deserve first-class aliases instead of nested-only access
- Medium priority / strong workflow payoff:
  - decide whether chart groups need richer per-group notes or status fields beyond claim text, element label, and analysis
- Lower priority / important for polish or validation:
  - document the legal limits of the helper-based date fields before extending them further, so the tool stays honest about what is heuristic versus legally definitive
  - define concrete acceptance targets for startup latency, first-query latency, and memory use on larger corpora
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

  - ~~synonym expansion with `synonym_of:"term"`~~ **done**
    - current implementation: `synonym_of:"term"|max=N|topics="..."` fetches Datamuse terms, saves them as a reusable in-memory term set, returns the used expansion in the query response, and both `synonym_of:` and later `termset:"term"` queries expand to ordinary `contains:` filters at parse time
    - justification / need-finding relation: even though broad synonym discovery often happens earlier in document-level search, this still provides a proof-of-concept for helping examiners when they lack comprehensive vocabulary coverage during passage-level analysis
    - remaining follow-up ideas:
      - add UI support that shows the Datamuse-expanded terms before the query runs
      - consider corpus-assisted suggestion from the currently selected documents as the next synonym-expansion layer
      - keep LLM-backed synonym suggestion optional and deferred, rather than making live query execution depend on it
      - avoid relying on general lexical resources like WordNet as the main solution, since they are likely too general and weak for patent-examiner workflows


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
