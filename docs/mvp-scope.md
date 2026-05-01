# MVP Scope

## Current State

- Constrained raw patent input formats (`.txt` and text-extractable `.pdf`)
- Fixed hierarchy: `Document -> Section -> Passage`
- Minimal metadata: `id`, `title`, `sourceFile`, `ingestedAt`
- Basic passage splitting by blank-line paragraphs, with passage ids and offsets
- Query filters:
  - `section:TYPE`
  - `contains:"phrase"`
  - `AND`
- Result output with:
  - matches grouped by document
  - matched passage text
  - section metadata
  - optional anchors (`paragraphId`, `claimNo`) when available
  - neighboring context
  - match reasons

## Goal Features

- Document-level metadata extraction (`doc_id`, dates, application number, inventors, CPC)
- Passage splitting with optional anchor extraction (`paragraphId`, `claimNo`)
- More Query filters:
  - `meta.KEY:"value"`
  - `cpc:"code"`
  - `paragraph:NNNN` (optional pinpoint filter, not primary retrieval)
  - `OR`
  - `NOT`
  - parentheses, precedence, nested expressions 
- Result output with optional anchors (`paragraphId`, `claimNo`) when available
- Pre-loading and lazy loading of documents to improve performance, speed and memory usage
  - Especially for larger document groups, both want to pre-load the docs we plan to search on (use early indicators?), 
  as well as avoid needlessly loading unnecessary documents to prevent wasted time querying them
- USPTO search integration
  - Chrome extension?
- Unique Query filters


### Additional Thoughts

- side-by-side interface between query dsl and hits in initial search query documents (set of documents our dsl will search over)
  - should support very fast indexing of all documents, very quickly adapting the search with fast refreshes (possibly 
  interesting work in determining a way to develop fast indexing of documents?)
  - ideally should nearly match the speed of autocorrect systems (nothing happens as you type, but once you stop for 
  a second or less, then updated results should appear)

- Most importantly, *include interesting features unique from current USPTO search query* capabilities
  - some feature overlaps can be fine due to enhancements from our interface vs USPTO search interface (passage-level 
  vs document-level search) and difference in part of workflow (find relevant potentially relevant docs -> determine 
  relevance of docs and find specific pieces of evidence)


### Stretchy Goals

- Semantic ranking models
- Cross-document joins
- Embedding-based retrieval




## Demo Goals

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