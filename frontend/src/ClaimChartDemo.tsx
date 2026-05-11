import { Fragment, useMemo, useState } from "react";

type EvidenceItem = {
  id: string;
  claim: string;
  reference: string;
  location: string;
  excerpt: string;
  reason: string;
};

const EVIDENCE_LIBRARY: EvidenceItem[] = [
  {
    id: "e1",
    claim: "Claim 1",
    reference: "Alicherry et al. (US 20130031559 A1)",
    location: "¶[0038]",
    excerpt:
      "The CAS 140 is configured to receive a user VM request requesting provisioning of VMs within cloud environment 110.",
    reason: "Supports the claim element about searching / requesting physical resources in a cloud environment.",
  },
  {
    id: "e2",
    claim: "Claim 1",
    reference: "Alicherry et al. (US 20130031559 A1)",
    location: "¶[0041]",
    excerpt:
      "The CAS 140 may be configured to determine assignment of requested VMs to physical resources of cloud environment 110.",
    reason: "Shows assignment to physical resources and supports the examiner's mapping rationale.",
  },
  {
    id: "e3",
    claim: "Claim 1",
    reference: "Shao et al. (US 20130060928 A1)",
    location: "¶[0034]",
    excerpt:
      "Cloud service requesters such as web service, application or user can access the cloud computing services and/or resources.",
    reason: "Used as secondary support for the access / user element.",
  },
];

type ChartRow = EvidenceItem & {
  elementText: string;
  notes: string;
};

export default function ClaimChartDemo() {
  const [rows, setRows] = useState<ChartRow[]>([]);
  const [copied, setCopied] = useState(false);

  const remainingEvidence = useMemo(
    () => EVIDENCE_LIBRARY.filter((item) => !rows.some((row) => row.id === item.id)),
    [rows]
  );

  function addRow(item: EvidenceItem) {
    setRows((current) => [
      ...current,
      {
        ...item,
        elementText: "",
        notes: item.reason,
      },
    ]);
  }

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
          <h2>Available Evidence</h2>
          <p className="subtitle">Mock passages based on the examiner-created chart you shared.</p>
          <div className="chartEvidenceList">
            {remainingEvidence.map((item) => (
              <article key={item.id} className="chartEvidenceCard">
                <div className="chartEvidenceMeta">
                  <strong>{item.reference}</strong>
                  <span>{item.location}</span>
                </div>
                <p><b>Excerpt:</b> {item.excerpt}</p>
                <p><b>Why it matters:</b> {item.reason}</p>
                <button type="button" className="chartActionButton" onClick={() => addRow(item)}>
                  Add to chart
                </button>
              </article>
            ))}
            {remainingEvidence.length === 0 ? <p className="subtitle">All mock evidence items have been added.</p> : null}
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
                <div key={`${row.id}-claim`} className="chartCell">{row.claim}</div>
                <div key={`${row.id}-element`} className="chartCell">
                  <textarea
                    className="chartTextarea"
                    rows={5}
                    value={row.elementText}
                    onChange={(event) => updateRow(row.id, "elementText", event.target.value)}
                    placeholder="Paste or type the claim element text here"
                  />
                </div>
                <div key={`${row.id}-reference`} className="chartCell">
                  <strong>{row.reference}</strong>
                  <div>{row.location}</div>
                  <button type="button" className="chartLinkButton" onClick={() => removeRow(row.id)}>
                    Remove
                  </button>
                </div>
                <div key={`${row.id}-notes`} className="chartCell">
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