# MVP Scope

## In Scope

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

## Out of Scope

- Embedding-based retrieval
- Semantic ranking models
- Claim dependency graphs
- Cross-document joins
- Full patent-format generality
- Rich query grammar (parentheses, precedence, nested expressions, OR/NOT)
- Paragraph-anchor-only workflows as the primary retrieval strategy
