import { FormEvent, useEffect, useMemo, useState } from "react";

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
      sectionType: string;
      sectionTitle: string;
      passageIndex: number;
      passageText: string;
      contextBefore: string | null;
      contextAfter: string | null;
      reasons: string[];
    }>;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:4000";

export default function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>("");
  const [queryText, setQueryText] = useState('section:SPECIFICATION AND contains:"signal processing"');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);

  useEffect(() => {
    void loadDocuments();
  }, []);

  const selectedDoc = useMemo(
    () => documents.find((doc) => doc.id === selectedDocumentId) ?? null,
    [documents, selectedDocumentId]
  );

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_BASE}/documents`);
      if (!response.ok) throw new Error(`Failed to load documents: ${response.status}`);
      const data = (await response.json()) as { documents: DocumentSummary[] };
      setDocuments(data.documents);

      if (data.documents.length > 0) {
        setSelectedDocumentId((current) => current || data.documents[0].id);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedDocumentId) {
      setError("Select a document first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          documentId: selectedDocumentId,
          queryText
        })
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? payload.detail ?? `Query failed: ${response.status}`);
      }

      setQueryResult(payload as QueryResponse);
    } catch (err) {
      setQueryResult(null);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Patent Query Prototype</h1>
        <p className="subtitle">Document → Section → Passage querying with a minimal DSL.</p>

        <form onSubmit={onSubmit} className="queryForm">
          <label>
            Document
            <select
              value={selectedDocumentId}
              onChange={(event) => setSelectedDocumentId(event.target.value)}
            >
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title} ({doc.id})
                </option>
              ))}
            </select>
          </label>

          <label>
            Query DSL
            <textarea
              rows={3}
              value={queryText}
              onChange={(event) => setQueryText(event.target.value)}
              spellCheck={false}
            />
          </label>

          <button type="submit" disabled={loading || !selectedDocumentId}>
            {loading ? "Running..." : "Run Query"}
          </button>
        </form>

        {selectedDoc ? (
          <p className="docMeta">
            Source: <code>{selectedDoc.sourceFile}</code> · Loaded: {new Date(selectedDoc.ingestedAt).toLocaleString()}
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
          {queryResult?.result.matches.map((match) => (
            <article key={match.passageId} className="resultCard">
              <header>
                <strong>{match.sectionType}</strong>
                <span>{match.sectionTitle}</span>
                <span>Passage {match.passageIndex}</span>
              </header>

              <p>{match.passageText}</p>

              <details>
                <summary>Context + match reasons</summary>
                <div className="contextBlock">
                  <p>
                    <b>Before:</b> {match.contextBefore ?? "(none)"}
                  </p>
                  <p>
                    <b>After:</b> {match.contextAfter ?? "(none)"}
                  </p>
                  <p>
                    <b>Reasons:</b> {match.reasons.join("; ")}
                  </p>
                </div>
              </details>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
