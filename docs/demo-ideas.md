# Demo Ideas

This file captures a compact demo plan for the current prototype so someone who has not watched the feature work evolve can still record a clear walkthrough.

## One-Minute Demo

### Goal

Show that the system is not just another document-level patent search UI. The key point is that patents are parsed into structured, queryable data and searched at the passage level with a DSL.

### Suggested Flow

1. Start on the main search page and show that the corpus now includes a larger multi-document set rather than a tiny toy example.
2. Point out that the user is choosing a document set first, then running a DSL query over structured patent content.
3. Run a query that shows section-aware passage retrieval, for example:

```text
section:DESCRIPTION AND termset:"virtual machine"
```

4. Show that the results are passages, not just document titles, and that each result carries section/title context and provenance.
5. Refine the query live to show iterative search, for example:

```text
section:DESCRIPTION AND termset:"virtual machine" AND heading:"Detailed Description"
```

6. Use `Add to chart` on one result to show that search is directly connected to claim mapping rather than ending at retrieval.
7. Switch to the claim-chart page and show that the evidence row arrived in the grouped chart workspace.

## Features Worth Highlighting

- Multi-document passage-level retrieval instead of document-level hit lists.
- Section-aware filtering with `section:`.
- Heading-aware filtering with `heading:` / `sectionTitle:`.
- Pinpoint structural filters such as `paragraph:`, `claim:`, and `figure:`.
- Metadata-aware filtering such as `meta.filingDate:<...`, `meta.assigneeName:~...`, and `cpc:"..."`.
- Reusable synonym expansion with `synonym_of:` and `termset:`.
- Claim-chart handoff with `Copy citation` and `Add to chart`.
- Live refinement behavior after interaction begins.

## Good Demo Queries

```text
section:DESCRIPTION AND termset:"virtual machine"
```

```text
heading:"Detailed Description" AND contains:"virtual network"
```

```text
meta.assigneeName:~"Google" AND section:DESCRIPTION AND contains:"migration"
```

```text
claim:8
```

```text
figure:"FIG. 2"
```

## What To Say

- "The novelty is that the query language operates over patent structure, metadata, and passage anchors rather than only over full-document text."
- "This supports the actual examiner workflow after retrieval: narrowing to the right passages, identifying evidence, and handing that evidence into a claim-mapping workspace."
- "The system addresses a subset of the needs from our inquiry study, especially synonym support, filing-date filtering, section-aware relevance assessment, and search-to-claim-mapping handoff."

## If Time Is Tight

If the demo must be extremely short, keep only this sequence:

1. Show corpus selection.
2. Run `section:DESCRIPTION AND termset:"virtual machine"`.
3. Add one result to the chart.
4. Open the chart and show the transferred evidence.