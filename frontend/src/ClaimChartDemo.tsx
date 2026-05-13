import { useEffect, useMemo, useState } from "react";
import { ChartRow, loadChartRows, saveChartRows } from "./claimChartStorage";

type ClaimElementGroup = {
  id: string;
  claim: string;
  elementLabel: string;
  elementText: string;
  rows: ChartRow[];
};

export default function ClaimChartDemo() {
  const [rows, setRows] = useState<ChartRow[]>(() => loadChartRows());
  const [copied, setCopied] = useState(false);

  const groupedRows = useMemo(() => groupChartRows(rows), [rows]);

  useEffect(() => {
    saveChartRows(rows);
  }, [rows]);

  useEffect(() => {
    function handleStorage(event: StorageEvent) {
      if (event.key === null || event.key === "claim-chart-rows") {
        setRows(loadChartRows());
      }
    }

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  function removeRow(id: string) {
    setRows((current) => current.filter((row) => row.id !== id));
  }

  function updateRow(id: string, field: "notes", value: string) {
    setRows((current) => current.map((row) => (row.id === id ? { ...row, [field]: value } : row)));
  }

  function updateGroup(groupId: string, field: "claim" | "elementLabel" | "elementText", value: string) {
    setRows((current) =>
      current.map((row) => (groupIdForRow(row) === groupId ? { ...row, [field]: value } : row))
    );
  }

  async function copyChartRows() {
    const lines = ["Claim\tElement label\tClaim element text\tCitation\tExcerpt\tAnalysis"];
    const text = lines
      .concat(
        groupedRows.flatMap((group) =>
          group.rows.map((row) =>
            [
              group.claim,
              group.elementLabel || "(fill element label)",
              group.elementText || "(fill claim element)",
              row.citation,
              row.excerpt,
              row.notes,
            ].join("\t")
          )
        )
      )
      .join("\n");

    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <main className="chartDemoPage">
      <section className="panel chartDemoIntro">
        <h1>Claim Chart Demo</h1>
        <p className="subtitle">
          A separate mock workflow for collecting evidence into a lightweight claim chart. <a href="#">Back to search →</a>
        </p>
      </section>

      <section className="chartDemoLayout">
        <div className="panel chartDemoColumn">
          <h2>Saved Evidence</h2>
          <p className="subtitle">Results added from the main search page appear here and stay editable in this separate workspace.</p>
          <div className="chartEvidenceList">
            {rows.map((item) => (
              <article key={item.id} className="chartEvidenceCard">
                <div className="chartEvidenceMeta">
                  <strong>{item.reference}</strong>
                  <span>{item.location}</span>
                  <span>{item.citation}</span>
                </div>
                <p><b>Excerpt:</b> {item.excerpt}</p>
                <p><b>Why it matters:</b> {item.reason}</p>
                <button type="button" className="chartActionButton" onClick={() => removeRow(item.id)}>
                  Remove from chart
                </button>
              </article>
            ))}
            {rows.length === 0 ? <p className="subtitle">No saved evidence yet. Add passages from search results with the new Add to chart action.</p> : null}
          </div>
        </div>

        <div className="panel chartDemoColumn">
          <div className="chartWorkspaceHeader">
            <div>
              <h2>Claim Chart Workspace</h2>
              <p className="subtitle">Rows with the same claim and element label are grouped under one claim element with separate evidence entries beneath it.</p>
            </div>
            <button type="button" className="chartActionButton" onClick={() => void copyChartRows()} disabled={rows.length === 0}>
              {copied ? "Copied rows" : "Copy rows as TSV"}
            </button>
          </div>

          <div className="chartGroupList">
            {groupedRows.map((group) => (
              <section key={group.id} className="chartGroupCard">
                <div className="chartGroupHeader">
                  <div className="chartGroupFields">
                    <label className="chartFieldLabel">
                      Claim
                      <input
                        className="chartInput"
                        value={group.claim}
                        onChange={(event) => updateGroup(group.id, "claim", event.target.value)}
                        placeholder="Claim 1"
                      />
                    </label>
                    <label className="chartFieldLabel">
                      Element label
                      <input
                        className="chartInput"
                        value={group.elementLabel}
                        onChange={(event) => updateGroup(group.id, "elementLabel", event.target.value)}
                        placeholder="Element 1[a]"
                      />
                    </label>
                  </div>
                  <div className="chartGroupCount">{group.rows.length} evidence {group.rows.length === 1 ? "row" : "rows"}</div>
                </div>

                <label className="chartFieldLabel">
                  Claim element text
                  <textarea
                    className="chartTextarea"
                    rows={4}
                    value={group.elementText}
                    onChange={(event) => updateGroup(group.id, "elementText", event.target.value)}
                    placeholder="Paste or type the claim element text here"
                  />
                </label>

                <div className="chartGroupEvidenceList">
                  {group.rows.map((row) => (
                    <article key={row.id} className="chartGroupEvidenceCard">
                      <details className="chartEvidenceDisclosure">
                        <summary className="chartEvidenceSummary">
                          <div className="chartGroupEvidenceMeta">
                            <strong>{row.citation}</strong>
                            <span>{row.reference}</span>
                          </div>
                          <p className="chartEvidencePreview">{previewExcerpt(row.excerpt)}</p>
                        </summary>

                        <div className="chartEvidenceDetail">
                          <p className="chartExcerpt">{row.excerpt || "No excerpt saved for this row."}</p>
                          <label className="chartFieldLabel">
                            Analysis
                            <textarea
                              className="chartTextarea"
                              rows={5}
                              value={row.notes}
                              onChange={(event) => updateRow(row.id, "notes", event.target.value)}
                              placeholder="Explain why this citation supports the claim element"
                            />
                          </label>
                          <button type="button" className="chartLinkButton" onClick={() => removeRow(row.id)}>
                            Remove evidence
                          </button>
                        </div>
                      </details>
                    </article>
                  ))}
                </div>
              </section>
            ))}
          </div>

          {rows.length === 0 ? <p className="subtitle">No chart rows yet. Add an evidence item from the left.</p> : null}
        </div>
      </section>
    </main>
  );
}

function previewExcerpt(excerpt: string) {
  const trimmed = excerpt.trim();
  if (!trimmed) {
    return "No excerpt saved for this row.";
  }

  if (trimmed.length <= 180) {
    return trimmed;
  }

  return `${trimmed.slice(0, 177).trimEnd()}...`;
}

function groupChartRows(rows: ChartRow[]): ClaimElementGroup[] {
  const groups = new Map<string, ClaimElementGroup>();

  for (const row of rows) {
    const groupId = groupIdForRow(row);
    const existing = groups.get(groupId);

    if (existing) {
      existing.rows.push(row);
      continue;
    }

    groups.set(groupId, {
      id: groupId,
      claim: row.claim,
      elementLabel: row.elementLabel,
      elementText: row.elementText,
      rows: [row],
    });
  }

  return [...groups.values()];
}

function groupIdForRow(row: ChartRow) {
  const claim = row.claim.trim().toLowerCase();
  const elementLabel = row.elementLabel.trim().toLowerCase();

  if (!claim || !elementLabel) {
    return row.id;
  }

  return `${claim}::${elementLabel}`;
}