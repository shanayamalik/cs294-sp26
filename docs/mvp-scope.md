# MVP Scope

## In Scope

- Constrained raw patent input formats (`.txt` and text-extractable `.pdf`)
- Fixed hierarchy: `Document -> Section -> Passage`
- Paragraph-level passage splitting
- Query filters:
  - `section:TYPE`
  - `contains:"phrase"`
  - `AND`
- Result output with:
  - matched passage text
  - section metadata
  - neighboring context
  - match reasons

## Out of Scope

- Embedding-based retrieval
- Semantic ranking models
- Claim decomposition and dependency graphs
- Cross-document joins
- Full patent-format generality
- Rich query grammar (parentheses, precedence, nested expressions)
