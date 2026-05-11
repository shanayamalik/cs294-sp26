import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

type DocumentSummary = {
  id: string;
  title: string;
  sourceFile: string;
  ingestedAt: string;
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

export default function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [queryText, setQueryText] = useState('section:SPECIFICATION AND contains:"signal processing"');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [submittedQueryText, setSubmittedQueryText] = useState("");
  const [copiedCitationKey, setCopiedCitationKey] = useState<string | null>(null);

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

  const highlightTerms = useMemo(() => extractHighlightTerms(submittedQueryText), [submittedQueryText]);

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
  const copiedCitationTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void runQuery(selectedDocumentIds, queryText);
    }, 600);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [queryText, selectedDocumentIds, runQuery]);

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
    setSelectedDocumentIds((current) =>
      current.includes(documentId) ? current.filter((id) => id !== documentId) : [...current, documentId]
    );
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

  function previewPassage(text: string) {
    if (text.length <= PASSAGE_PREVIEW_LIMIT) {
      return text;
    }

    const truncated = text.slice(0, PASSAGE_PREVIEW_LIMIT);
    const lastSpace = truncated.lastIndexOf(" ");
    return `${truncated.slice(0, lastSpace > 280 ? lastSpace : PASSAGE_PREVIEW_LIMIT).trim()}...`;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (selectedDocumentIds.length === 0) {
      setError("Select at least one document first.");
      return;
    }
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
            <div className="documentPickerActions">
              <button type="button" className="secondaryButton" onClick={() => setSelectedDocumentIds(documents.map((doc) => doc.id))}>
                Select all
              </button>
              <button type="button" className="secondaryButton" onClick={() => setSelectedDocumentIds([])}>
                Clear
              </button>
            </div>
            <div className="documentOptions">
              {documents.map((doc) => (
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
            </div>
          </fieldset>

          <label>
            Query DSL
            <textarea
              rows={3}
              value={queryText}
              onChange={(event) => setQueryText(event.target.value)}
              spellCheck={false}
            />
          </label>

          <button type="submit" disabled={loading || selectedDocumentIds.length === 0}>
            {loading ? "Running..." : "Run Query"}
          </button>
        </form>

        {selectedDocuments.length > 0 ? (
          <p className="docMeta">
            Searching {selectedDocuments.length} of {documents.length} document(s):{" "}
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

            return (
              <article key={`${match.documentId}:${match.passageId}`} className="resultCard">
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
                  <button
                    type="button"
                    className="copyCitationButton"
                    onClick={() => void copyCitation(match, documentTitle)}
                  >
                    {copiedCitationKey === `${match.documentId}:${match.passageId}` ? "Copied" : "Copy citation"}
                  </button>
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

function extractHighlightTerms(queryText: string) {
  const terms: string[] = [];

  for (const clause of splitQueryClauses(queryText)) {
    const containsMatch = clause.match(/^contains\s*:\s*(?:"([^"]+)"|(.+))$/i);
    if (containsMatch) {
      terms.push((containsMatch[1] ?? containsMatch[2] ?? "").trim());
      continue;
    }

    const metadataMatch = clause.match(/^(?:meta|metadata)\.[A-Za-z0-9_.-]+\s*:\s*(?:"([^"]+)"|(.+))$/i);
    if (metadataMatch) {
      terms.push((metadataMatch[1] ?? metadataMatch[2] ?? "").trim());
      continue;
    }

    const elementMatch = clause.match(/^(?:cpc|paragraph|claim|figure)\s*:\s*(?:"([^"]+)"|(.+))$/i);
    if (elementMatch) {
      terms.push((elementMatch[1] ?? elementMatch[2] ?? "").trim());
    }
  }

  return [...new Map(terms.filter(Boolean).map((term) => [term.toLowerCase(), term])).values()].sort(
    (left, right) => right.length - left.length
  );
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

function highlightText(text: string, terms: string[]): ReactNode {
  if (terms.length === 0) {
    return text;
  }

  const pattern = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "gi");
  return text.split(pattern).map((part, index) =>
    terms.some((term) => term.toLowerCase() === part.toLowerCase()) ? (
      <mark key={`${part}-${index}`} className="queryHighlight">
        {part}
      </mark>
    ) : (
      part
    )
  );
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
