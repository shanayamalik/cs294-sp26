# MVP Scope

## Presentation goals?

- Constrained raw patent input formats (`.txt` and text-extractable `.pdf`)
- Fixed hierarchy: `Document -> Section -> Passage`
- Document-level metadata extraction (`doc_id`, dates, application number, inventors, CPC)
- Passage splitting with optional anchor extraction (`paragraphId`, `claimNo`)
- Query filters:
  - `section:TYPE`
  - `meta.KEY:"value"`
  - `cpc:"code"`
  - `contains:"phrase"`
  - `paragraph:NNNN` (optional pinpoint filter, not primary retrieval)
  - `AND`
- Result output with:
  - matches grouped by document
  - matched passage text
  - section metadata
  - optional anchors (`paragraphId`, `claimNo`) when available
  - neighboring context
  - match reasons

## Some final paper feature goals

- Embedding-based retrieval
- Semantic ranking models
- Cross-document joins
- Rich query grammar (parentheses, precedence, nested expressions, OR/NOT)
- USPTO search integration
