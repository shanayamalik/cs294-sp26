import { Dispatch, FormEvent, ReactNode, SetStateAction, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChartRow, clearSearchNavigationTarget, loadSearchNavigationTarget, upsertChartRow } from "./claimChartStorage";

type DocumentSummary = {
  id: string;
  title: string;
  sourceFile: string;
  ingestedAt: string;
  assigneeName: string | null;
  inventorNames: string[] | null;
};

type QueryResponse = {
  result: {
    totalMatches: number;
    matches: Array<{
      passageId: string;
      documentId: string;
      sectionType: string;
      sectionTitle: string;
      passageIndex: number;
      passageText: string;
      contextBefore: string | null;
      contextAfter: string | null;
      reasons: string[];
      paragraphId: string | null;
      claimNo: number | null;
    }>;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:4000";
const PASSAGE_PREVIEW_LIMIT = 420;
const INLINE_FACET_LIMIT = 5;

type HighlightTerm = {
  value: string;
  allowRegex: boolean;
};

type HighlightSpan = {
  start: number;
  end: number;
};

export default function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [selectedAssigneeFacets, setSelectedAssigneeFacets] = useState<string[]>([]);
  const [selectedInventorFacets, setSelectedInventorFacets] = useState<string[]>([]);
  const [assigneeFacetQuery, setAssigneeFacetQuery] = useState("");
  const [inventorFacetQuery, setInventorFacetQuery] = useState("");
  const [queryText, setQueryText] = useState('section:SPECIFICATION AND contains:"signal processing"');
  const [liveQueryEnabled, setLiveQueryEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [submittedQueryText, setSubmittedQueryText] = useState("");
  const [copiedCitationKey, setCopiedCitationKey] = useState<string | null>(null);
  const [savedToChartKey, setSavedToChartKey] = useState<string | null>(null);
  const [focusedResultKey, setFocusedResultKey] = useState<string | null>(null);
  const [pendingSearchNavigation, setPendingSearchNavigation] = useState(() => loadSearchNavigationTarget());

  useEffect(() => {
    void loadDocuments();
  }, []);

  const documentsById = useMemo(
    () => new Map(documents.map((doc) => [doc.id, doc])),
    [documents]
  );

  const selectedDocuments = useMemo(
    () => selectedDocumentIds.map((id) => documentsById.get(id)).filter((doc): doc is DocumentSummary => Boolean(doc)),
    [documentsById, selectedDocumentIds]
  );

  const assigneeFacets = useMemo(() => uniqueSortedValues(documents.map((doc) => doc.assigneeName)), [documents]);
  const inventorFacets = useMemo(
    () => uniqueSortedValues(documents.flatMap((doc) => doc.inventorNames ?? [])),
    [documents]
  );

  const filteredAssigneeFacets = useMemo(
    () => filterFacetValues(assigneeFacets, assigneeFacetQuery),
    [assigneeFacets, assigneeFacetQuery]
  );

  const filteredInventorFacets = useMemo(
    () => filterFacetValues(inventorFacets, inventorFacetQuery),
    [inventorFacets, inventorFacetQuery]
  );

  const visibleAssigneeFacets = useMemo(() => {
    if (assigneeFacets.length <= INLINE_FACET_LIMIT || assigneeFacetQuery.trim()) {
      return filteredAssigneeFacets;
    }

    return assigneeFacets.slice(0, INLINE_FACET_LIMIT);
  }, [assigneeFacetQuery, assigneeFacets, filteredAssigneeFacets]);

  const visibleInventorFacets = useMemo(() => {
    if (inventorFacets.length <= INLINE_FACET_LIMIT || inventorFacetQuery.trim()) {
      return filteredInventorFacets;
    }

    return inventorFacets.slice(0, INLINE_FACET_LIMIT);
  }, [filteredInventorFacets, inventorFacetQuery, inventorFacets]);

  const visibleDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesAssignee =
        selectedAssigneeFacets.length === 0 || (doc.assigneeName != null && selectedAssigneeFacets.includes(doc.assigneeName));
      const matchesInventor =
        selectedInventorFacets.length === 0 || (doc.inventorNames ?? []).some((name) => selectedInventorFacets.includes(name));
      return matchesAssignee && matchesInventor;
    });
  }, [documents, selectedAssigneeFacets, selectedInventorFacets]);

  const visibleDocumentIds = useMemo(() => new Set(visibleDocuments.map((doc) => doc.id)), [visibleDocuments]);

  const highlightTerms = useMemo(() => extractHighlightTerms(submittedQueryText), [submittedQueryText]);

  useEffect(() => {
    if (selectedAssigneeFacets.length === 0 && selectedInventorFacets.length === 0) {
      return;
    }

    setSelectedDocumentIds((current) => current.filter((id) => visibleDocumentIds.has(id)));
  }, [selectedAssigneeFacets, selectedInventorFacets, visibleDocumentIds]);

  const runQuery = useCallback(async (docIds: string[], text: string) => {
    if (docIds.length === 0 || !text.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ documentIds: docIds, queryText: text }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? payload.detail ?? `Query failed: ${response.status}`);
      }

      setQueryResult(payload as QueryResponse);
      setSubmittedQueryText(text);
    } catch (err) {
      setQueryResult(null);
      setSubmittedQueryText("");
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const preloadDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const copiedCitationTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const savedToChartTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const preloadDocuments = useCallback(async (docIds: string[]) => {
    if (docIds.length === 0) {
      return;
    }

    try {
      await fetch(`${API_BASE}/documents/preload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ documentIds: docIds }),
      });
    } catch {
      // Preloading is opportunistic; query execution remains the source of truth.
    }
  }, []);

  useEffect(() => {
    if (documents.length === 0) {
      return;
    }

    const target = pendingSearchNavigation;
    if (!target) {
      return;
    }

    const nextDocumentIds = target.documentIds.filter((id) => documentsById.has(id));
    if (nextDocumentIds.length === 0) {
      clearSearchNavigationTarget();
      setPendingSearchNavigation(null);
      return;
    }

    setSelectedDocumentIds(nextDocumentIds);
    setQueryText(target.queryText);
    setLiveQueryEnabled(true);
    setFocusedResultKey(target.resultKey);
    setPendingSearchNavigation(null);
    void preloadDocuments(nextDocumentIds);
    void runQuery(nextDocumentIds, target.queryText);
  }, [documents.length, documentsById, pendingSearchNavigation, preloadDocuments, runQuery]);

  useEffect(() => {
    if (!liveQueryEnabled) {
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void runQuery(selectedDocumentIds, queryText);
    }, 600);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [liveQueryEnabled, queryText, selectedDocumentIds, runQuery]);

  useEffect(() => {
    if (!liveQueryEnabled || selectedDocumentIds.length === 0) {
      return;
    }

    if (preloadDebounceRef.current) clearTimeout(preloadDebounceRef.current);
    preloadDebounceRef.current = setTimeout(() => {
      void preloadDocuments(selectedDocumentIds);
    }, 250);

    return () => {
      if (preloadDebounceRef.current) clearTimeout(preloadDebounceRef.current);
    };
  }, [liveQueryEnabled, preloadDocuments, selectedDocumentIds]);

  useEffect(() => {
    if (!focusedResultKey) {
      return;
    }

    const element = document.getElementById(resultElementId(focusedResultKey));
    if (!element) {
      return;
    }

    clearSearchNavigationTarget();
    element.scrollIntoView({ behavior: "smooth", block: "center" });

    const timeout = window.setTimeout(() => setFocusedResultKey(null), 5000);
    return () => window.clearTimeout(timeout);
  }, [focusedResultKey, queryResult]);

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_BASE}/documents`);
      if (!response.ok) throw new Error(`Failed to load documents: ${response.status}`);
      const data = (await response.json()) as { documents: DocumentSummary[] };
      setDocuments(data.documents);

      if (data.documents.length > 0) {
        setSelectedDocumentIds((current) =>
          current.length > 0 ? current.filter((id) => data.documents.some((doc) => doc.id === id)) : data.documents.map((doc) => doc.id)
        );
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function toggleDocument(documentId: string) {
    setLiveQueryEnabled(true);
    setSelectedDocumentIds((current) =>
      current.includes(documentId) ? current.filter((id) => id !== documentId) : [...current, documentId]
    );
  }

  function selectAllDocuments() {
    setLiveQueryEnabled(true);
    setSelectedDocumentIds(visibleDocuments.map((doc) => doc.id));
  }

  function clearDocuments() {
    setLiveQueryEnabled(true);
    setSelectedDocumentIds([]);
  }

  function toggleFacet(value: string, setFacetState: Dispatch<SetStateAction<string[]>>) {
    setFacetState((current) => (current.includes(value) ? current.filter((item) => item !== value) : [...current, value]));
  }

  function clearMetadataFacets() {
    setSelectedAssigneeFacets([]);
    setSelectedInventorFacets([]);
    setAssigneeFacetQuery("");
    setInventorFacetQuery("");
  }

  async function copyCitation(match: QueryResponse["result"]["matches"][number], documentTitle: string) {
    const citation = formatCitation(match, documentTitle);

    try {
      await navigator.clipboard.writeText(citation);
      const matchKey = `${match.documentId}:${match.passageId}`;
      setCopiedCitationKey(matchKey);
      if (copiedCitationTimeoutRef.current) clearTimeout(copiedCitationTimeoutRef.current);
      copiedCitationTimeoutRef.current = setTimeout(() => setCopiedCitationKey(null), 1600);
    } catch {
      setError("Failed to copy citation.");
    }
  }

  function addMatchToChart(match: QueryResponse["result"]["matches"][number], documentTitle: string) {
    try {
      const chartRow = createChartRow(match, documentTitle, queryText, selectedDocumentIds);
      upsertChartRow(chartRow);

      const matchKey = `${match.documentId}:${match.passageId}`;
      setSavedToChartKey(matchKey);
      if (savedToChartTimeoutRef.current) clearTimeout(savedToChartTimeoutRef.current);
      savedToChartTimeoutRef.current = setTimeout(() => setSavedToChartKey(null), 1600);
    } catch {
      setError("Failed to add result to claim chart.");
    }
  }

  function previewPassage(text: string) {
    if (text.length <= PASSAGE_PREVIEW_LIMIT) {
      return text;
    }

    const truncated = text.slice(0, PASSAGE_PREVIEW_LIMIT);
    const lastSpace = truncated.lastIndexOf(" ");
    return `${truncated.slice(0, lastSpace > 280 ? lastSpace : PASSAGE_PREVIEW_LIMIT).trim()}...`;
  }

  function goToChart() {
    window.location.hash = "#claim-chart-demo";
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (selectedDocumentIds.length === 0) {
      setError("Select at least one document first.");
      return;
    }

    setLiveQueryEnabled(true);
    void preloadDocuments(selectedDocumentIds);
    void runQuery(selectedDocumentIds, queryText);
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Patent Query Prototype</h1>
        <p className="subtitle">
          Document → Section → Passage querying with a minimal DSL. {" "}
          <a href="#claim-chart-demo">Try claim chart demo →</a>
        </p>

        <form onSubmit={onSubmit} className="queryForm">
          <fieldset className="documentPicker">
            <legend>Documents</legend>
            {assigneeFacets.length > 0 ? (
              <div className="facetBlock">
                <div className="facetHeader">
                  <span>Assignee facets</span>
                  <span className="facetHint">Type to find a specific assignee</span>
                </div>
                <input
                  className="facetSearchInput"
                  value={assigneeFacetQuery}
                  onChange={(event) => setAssigneeFacetQuery(event.target.value)}
                  placeholder="Filter assignees"
                />
                <div className="facetChips">
                  {visibleAssigneeFacets.map((assigneeName) => {
                    const active = selectedAssigneeFacets.includes(assigneeName);
                    return (
                      <button
                        key={assigneeName}
                        type="button"
                        className={`facetChip${active ? " facetChipActive" : ""}`}
                        onClick={() => toggleFacet(assigneeName, setSelectedAssigneeFacets)}
                      >
                        {assigneeName}
                      </button>
                    );
                  })}
                </div>
                {assigneeFacets.length > INLINE_FACET_LIMIT && !assigneeFacetQuery.trim() ? (
                  <p className="facetHint">Showing the first {INLINE_FACET_LIMIT} assignees. Type to narrow the full list.</p>
                ) : null}
                {assigneeFacetQuery.trim() && visibleAssigneeFacets.length === 0 ? (
                  <p className="facetHint">No assignees match that filter.</p>
                ) : null}
              </div>
            ) : null}
            {inventorFacets.length > 0 ? (
              <div className="facetBlock">
                <div className="facetHeader">
                  <span>Inventor facets</span>
                  <span className="facetHint">Type to find a specific inventor</span>
                </div>
                <input
                  className="facetSearchInput"
                  value={inventorFacetQuery}
                  onChange={(event) => setInventorFacetQuery(event.target.value)}
                  placeholder="Filter inventors"
                />
                <div className="facetChips facetChipsScrollable">
                  {visibleInventorFacets.map((inventorName) => {
                    const active = selectedInventorFacets.includes(inventorName);
                    return (
                      <button
                        key={inventorName}
                        type="button"
                        className={`facetChip${active ? " facetChipActive" : ""}`}
                        onClick={() => toggleFacet(inventorName, setSelectedInventorFacets)}
                      >
                        {inventorName}
                      </button>
                    );
                  })}
                </div>
                {inventorFacets.length > INLINE_FACET_LIMIT && !inventorFacetQuery.trim() ? (
                  <p className="facetHint">Showing the first {INLINE_FACET_LIMIT} inventors. Type to narrow the full list.</p>
                ) : null}
                {inventorFacetQuery.trim() && visibleInventorFacets.length === 0 ? <p className="facetHint">No inventors match that filter.</p> : null}
              </div>
            ) : null}
            <div className="documentPickerActions">
              <button type="button" className="secondaryButton" onClick={selectAllDocuments}>
                Select visible
              </button>
              <button type="button" className="secondaryButton" onClick={clearDocuments}>
                Clear
              </button>
              <button
                type="button"
                className="secondaryButton"
                onClick={clearMetadataFacets}
                disabled={selectedAssigneeFacets.length === 0 && selectedInventorFacets.length === 0}
              >
                Clear facets
              </button>
            </div>
            <div className="documentOptions">
              {visibleDocuments.map((doc) => (
                <label key={doc.id} className="documentOption">
                  <input
                    type="checkbox"
                    checked={selectedDocumentIds.includes(doc.id)}
                    onChange={() => toggleDocument(doc.id)}
                  />
                  <span>
                    <strong>{doc.title}</strong>
                    <code>{doc.id}</code>
                  </span>
                </label>
              ))}
              {visibleDocuments.length === 0 ? <p className="subtitle">No documents match the current metadata facets.</p> : null}
            </div>
          </fieldset>

          <label>
            Query DSL
            <textarea
              rows={3}
              value={queryText}
              onChange={(event) => {
                setLiveQueryEnabled(true);
                setQueryText(event.target.value);
              }}
              spellCheck={false}
            />
          </label>

          <button type="submit" disabled={loading || selectedDocumentIds.length === 0}>
            {loading ? "Running..." : "Run Query"}
          </button>
        </form>

        {selectedDocuments.length > 0 ? (
          <p className="docMeta">
            Searching {selectedDocuments.length} of {visibleDocuments.length} visible / {documents.length} total document(s):{" "}
            {selectedDocuments.map((doc) => doc.id).join(", ")}
          </p>
        ) : null}

        {error ? <div className="error">{error}</div> : null}
      </section>

      <section className="panel">
        <h2>Results</h2>
        <p className="subtitle">
          {queryResult ? `${queryResult.result.totalMatches} match(es)` : "Run a query to inspect passages."}
        </p>

        <div className="results">
          {queryResult?.result.matches.map((match) => {
            const documentTitle = documentsById.get(match.documentId)?.title ?? match.documentId;
            const resultKey = `${match.documentId}:${match.passageId}`;

            return (
              <article
                key={resultKey}
                id={resultElementId(resultKey)}
                className={`resultCard${focusedResultKey === resultKey ? " focusedResult" : ""}`}
              >
                <header>
                  <span className="documentLabel">
                    {highlightText(documentTitle, highlightTerms)}
                    <code>{highlightText(match.documentId, highlightTerms)}</code>
                  </span>
                  <strong>{match.sectionType}</strong>
                  <span>{highlightText(match.sectionTitle, highlightTerms)}</span>
                  <span>Passage {match.passageIndex}</span>
                  {match.paragraphId != null ? <span className="anchor">¶[{match.paragraphId}]</span> : null}
                  {match.claimNo != null ? <span className="anchor">Claim {match.claimNo}</span> : null}
                  <div className="resultActions">
                    <button
                      type="button"
                      className="copyCitationButton"
                      onClick={() => void copyCitation(match, documentTitle)}
                    >
                      {copiedCitationKey === resultKey ? "Copied" : "Copy citation"}
                    </button>
                    <button
                      type="button"
                      className="copyCitationButton"
                      onClick={() => addMatchToChart(match, documentTitle)}
                    >
                      {savedToChartKey === resultKey ? "Added to chart" : "Add to chart"}
                    </button>
                    <button type="button" className="copyCitationButton" onClick={goToChart}>
                      View chart
                    </button>
                  </div>
                </header>

                <p className="passagePreview">{highlightText(previewPassage(match.passageText), highlightTerms)}</p>

                <details>
                  <summary>Full passage + context</summary>
                  <div className="contextBlock">
                    <p>
                      <b>Matched passage:</b> {highlightText(match.passageText, highlightTerms)}
                    </p>
                    <p>
                      <b>Before:</b> {match.contextBefore ? highlightText(match.contextBefore, highlightTerms) : "(none)"}
                    </p>
                    <p>
                      <b>After:</b> {match.contextAfter ? highlightText(match.contextAfter, highlightTerms) : "(none)"}
                    </p>
                    <p>
                      <b>Reasons:</b> {highlightText(match.reasons.join("; "), highlightTerms)}
                    </p>
                  </div>
                </details>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}

function formatCitation(match: QueryResponse["result"]["matches"][number], documentTitle: string) {
  const anchor = match.paragraphId != null ? `¶[${match.paragraphId}]` : match.claimNo != null ? `Claim ${match.claimNo}` : `Passage ${match.passageIndex}`;
  return `${documentTitle} (${match.documentId}), ${match.sectionType}${match.sectionTitle ? ` ${match.sectionTitle}` : ""}, ${anchor}`;
}

function createChartRow(
  match: QueryResponse["result"]["matches"][number],
  documentTitle: string,
  queryText: string,
  selectedDocumentIds: string[]
): ChartRow {
  const location = match.paragraphId != null ? `¶[${match.paragraphId}]` : match.claimNo != null ? `Claim ${match.claimNo}` : `Passage ${match.passageIndex}`;

  return {
    id: `${match.documentId}:${match.passageId}`,
    claim: match.claimNo != null ? `Claim ${match.claimNo}` : "Claim ?",
    elementLabel: "",
    reference: `${documentTitle} (${match.documentId})`,
    location,
    citation: formatCitation(match, documentTitle),
    excerpt: match.passageText,
    reason: match.reasons.join("; "),
    elementText: "",
    notes: `${match.sectionType}${match.sectionTitle ? ` ${match.sectionTitle}` : ""}, ${location}`,
    sourceDocumentIds: selectedDocumentIds,
    sourceQueryText: queryText,
    sourceResultKey: `${match.documentId}:${match.passageId}`,
  };
}

function resultElementId(resultKey: string) {
  return `result-${resultKey.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
}

function uniqueSortedValues(values: Array<string | null | undefined>) {
  return [...new Set(values.filter((value): value is string => Boolean(value && value.trim().length > 0)))].sort((left, right) =>
    left.localeCompare(right)
  );
}

function filterFacetValues(values: string[], query: string) {
  const trimmedQuery = query.trim();
  if (!trimmedQuery) {
    return values;
  }

  const normalizedQuery = trimmedQuery.toLocaleLowerCase();
  return values.filter((value) => value.toLocaleLowerCase().includes(normalizedQuery));
}

function extractHighlightTerms(queryText: string) {
  const terms: HighlightTerm[] = [];

  for (const clause of splitQueryClauses(queryText)) {
    const containsRegexMatch = clause.match(/^contains\.regex\s*:\s*(?:"([^"]+)"|(.+))$/i);
    if (containsRegexMatch) {
      terms.push({ value: (containsRegexMatch[1] ?? containsRegexMatch[2] ?? "").trim(), allowRegex: true });
      continue;
    }

    const containsMatch = clause.match(/^contains\s*:\s*(?:"([^"]+)"|(.+))$/i);
    if (containsMatch) {
      terms.push({ value: (containsMatch[1] ?? containsMatch[2] ?? "").trim(), allowRegex: false });
      continue;
    }

    const metadataMatch = clause.match(/^(?:meta|metadata)\.[A-Za-z0-9_.-]+\s*:\s*(?:"([^"]+)"|(.+))$/i);
    if (metadataMatch) {
      terms.push({ value: (metadataMatch[1] ?? metadataMatch[2] ?? "").trim(), allowRegex: false });
      continue;
    }

    const elementMatch = clause.match(/^(?:cpc|paragraph|claim|figure)\s*:\s*(?:"([^"]+)"|(.+))$/i);
    if (elementMatch) {
      terms.push({ value: (elementMatch[1] ?? elementMatch[2] ?? "").trim(), allowRegex: false });
    }
  }

  const uniqueTerms = new Map<string, HighlightTerm>();
  for (const term of terms.filter((term) => term.value)) {
    const key = term.value.toLowerCase();
    const existing = uniqueTerms.get(key);
    uniqueTerms.set(key, existing ? { ...existing, allowRegex: existing.allowRegex || term.allowRegex } : term);
  }

  return [...uniqueTerms.values()].sort((left, right) => right.value.length - left.value.length);
}

function splitQueryClauses(queryText: string) {
  return splitBooleanClauses(queryText, "OR")
    .flatMap((group) => splitBooleanClauses(group, "AND"))
    .map((clause) => stripNotOperators(clause))
    .filter(Boolean);
}

function splitBooleanClauses(queryText: string, operator: "AND" | "OR") {
  const clauses: string[] = [];
  let inQuotes = false;
  let current = "";

  for (let index = 0; index < queryText.length; index += 1) {
    const character = queryText[index];

    if (character === '"') {
      inQuotes = !inQuotes;
      current += character;
      continue;
    }

    if (!inQuotes && operatorAt(queryText, index, operator)) {
      const clause = current.trim();
      if (clause) clauses.push(clause);
      current = "";
      index += operator.length - 1;
      continue;
    }

    current += character;
  }

  const clause = current.trim();
  if (clause) clauses.push(clause);
  return clauses;
}

function operatorAt(queryText: string, index: number, operator: "AND" | "OR") {
  const end = index + operator.length;
  if (queryText.slice(index, end).toUpperCase() !== operator) {
    return false;
  }

  const before = index > 0 ? queryText[index - 1] : " ";
  const after = end < queryText.length ? queryText[end] : " ";
  return /\s/.test(before) && /\s/.test(after);
}

function stripNotOperators(clause: string) {
  let nextClause = clause.trim();

  while (/^NOT\s+/i.test(nextClause)) {
    nextClause = nextClause.replace(/^NOT\s+/i, "").trim();
  }

  return nextClause.replace(/^\(+\s*/, "").replace(/\s*\)+$/, "").trim();
}

function highlightText(text: string, terms: HighlightTerm[]): ReactNode {
  if (terms.length === 0) {
    return text;
  }

  const spans = collectHighlightSpans(text, terms);
  if (spans.length === 0) {
    return text;
  }

  const nodes: ReactNode[] = [];
  let cursor = 0;

  spans.forEach((span, index) => {
    if (span.start > cursor) {
      nodes.push(text.slice(cursor, span.start));
    }

    nodes.push(
      <mark key={`${span.start}-${span.end}-${index}`} className="queryHighlight">
        {text.slice(span.start, span.end)}
      </mark>
    );
    cursor = span.end;
  });

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return nodes;
}

function collectHighlightSpans(text: string, terms: HighlightTerm[]) {
  const spans: HighlightSpan[] = [];

  for (const term of terms) {
    if (term.allowRegex) {
      spans.push(...findRegexSpans(text, term.value));
      continue;
    }

    const literalMatches = findLiteralSpans(text, term.value);
    spans.push(...literalMatches);
  }

  return mergeHighlightSpans(spans);
}

function findLiteralSpans(text: string, term: string) {
  const spans: HighlightSpan[] = [];
  const normalizedText = text.toLowerCase();
  const normalizedTerm = term.toLowerCase();
  let index = normalizedText.indexOf(normalizedTerm);

  while (index !== -1) {
    spans.push({ start: index, end: index + term.length });
    index = normalizedText.indexOf(normalizedTerm, index + term.length);
  }

  return spans;
}

function findRegexSpans(text: string, pattern: string) {
  const spans: HighlightSpan[] = [];
  let regex: RegExp;

  try {
    regex = new RegExp(pattern, "gi");
  } catch {
    return spans;
  }

  let match: RegExpExecArray | null;
  while ((match = regex.exec(text)) !== null) {
    if (match[0].length === 0) {
      regex.lastIndex += 1;
      continue;
    }

    spans.push({ start: match.index, end: match.index + match[0].length });
  }

  return spans;
}

function mergeHighlightSpans(spans: HighlightSpan[]) {
  const ordered = [...spans].sort((left, right) => left.start - right.start || right.end - left.end);
  const merged: HighlightSpan[] = [];

  for (const span of ordered) {
    const last = merged[merged.length - 1];
    if (!last || span.start >= last.end) {
      merged.push(span);
    }
  }

  return merged;
}
