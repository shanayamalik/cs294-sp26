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
  - `section:TYPE`
  - `contains:"phrase"`
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
- Frontend uses 600ms debounced live refresh so result sets update during query refinement
- Separate `#claim-chart-demo` page provides an isolated claim-chart workspace with editable rows and TSV export
- Claim-chart demo persists saved rows in the browser so the search page and chart page stay connected without merging the workflows
- Demo corpus includes parsed sample patent data and multiple USPTO patent PDFs
- Supported demo queries are captured in [example-queries.md](example-queries.md)

## Goal Features

- More Query filters:
  - ~~`paragraph:NNNN` (optional pinpoint filter, not primary retrieval)~~ **done** 
- More *Unique* Query filters specific to examiner workflows that we can extract from need finding
- ~~Filing-date comparison / admissibility filters (for example `meta.filingDate:<2018-03-15`)~~ **done**
- Better metadata operators for inventor / assignee / date exploration
  - ~~substring / prefix matching, direct inventor / assignee name aliases, date convenience aliases, and derived priority / effective / admissibility date helpers~~ **done**
  - remaining work: richer inventor / assignee facets beyond name lookup and any future deeper legal refinement beyond the current helper-based date model
- Claim-mapping support built on top of retrieved passages
  - ~~copy citation button~~ **done**
  - ~~separate claim-chart demo page~~ **done**
  - ~~stronger chart structure, better claim-element editing, grouped multi-evidence claim elements, and TSV export closer to examiner charts~~ **done**
  - remaining work: examiner-style document export and smoother chart navigation / editing workflows
- shanaya (me) wouldlike to do UI polish / visual redesign
  - I will do these on a separate branch so u cans see if u like it and find it aesthetic before we merge
- Pre-loading and lazy loading of documents to improve performance, speed and memory usage
  - Especially for larger document groups, both want to pre-load the docs we plan to search on (use early indicators?), 
  as well as avoid needlessly loading unnecessary documents to prevent wasted time querying them
- USPTO search integration
  - Chrome/Browser extension?
  - API integration with [USPTO API](https://data.uspto.gov/apis/getting-started)


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