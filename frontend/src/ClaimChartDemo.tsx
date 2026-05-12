import { Fragment, useEffect, useState } from "react";
import { ChartRow, loadChartRows, saveChartRows } from "./claimChartStorage";

export default function ClaimChartDemo() {
  const [rows, setRows] = useState<ChartRow[]>(() => loadChartRows());
  const [copied, setCopied] = useState(false);

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

  function updateRow(id: string, field: "elementText" | "notes", value: string) {
    setRows((current) => current.map((row) => (row.id === id ? { ...row, [field]: value } : row)));
  }

  async function copyChartRows() {
    const text = rows
      .map((row) => [row.claim, row.elementText || "(fill claim element)", row.reference, row.location, row.excerpt, row.notes].join("\t"))
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
              <p className="subtitle">Each added item becomes one editable row candidate.</p>
            </div>
            <button type="button" className="chartActionButton" onClick={() => void copyChartRows()} disabled={rows.length === 0}>
              {copied ? "Copied rows" : "Copy rows as TSV"}
            </button>
          </div>

          <div className="chartTable">
            <div className="chartTableHeader">Claim</div>
            <div className="chartTableHeader">Claim element</div>
            <div className="chartTableHeader">Reference / anchor</div>
            <div className="chartTableHeader">Excerpt + notes</div>

            {rows.map((row) => (
              <Fragment key={row.id}>
                <div className="chartCell">{row.claim}</div>
                <div className="chartCell">
                  <textarea
                    className="chartTextarea"
                    rows={5}
                    value={row.elementText}
                    onChange={(event) => updateRow(row.id, "elementText", event.target.value)}
                    placeholder="Paste or type the claim element text here"
                  />
                </div>
                <div className="chartCell">
                  <strong>{row.reference}</strong>
                  <div>{row.location}</div>
                  <button type="button" className="chartLinkButton" onClick={() => removeRow(row.id)}>
                    Remove
                  </button>
                </div>
                <div className="chartCell">
                  <p className="chartExcerpt">{row.excerpt}</p>
                  <textarea
                    className="chartTextarea"
                    rows={6}
                    value={row.notes}
                    onChange={(event) => updateRow(row.id, "notes", event.target.value)}
                  />
                </div>
              </Fragment>
            ))}
          </div>

          {rows.length === 0 ? <p className="subtitle">No chart rows yet. Add an evidence item from the left.</p> : null}
        </div>
      </section>
    </main>
  );
}