import { useEffect, useMemo, useState } from "react";
import { ChartRow, loadChartRows, saveChartRows, saveSearchNavigationTarget } from "./claimChartStorage";
import { exportClaimChartDocx } from "./exportClaimChartDocx";

type ClaimElementGroup = {
  id: string;
  claim: string;
  elementLabel: string;
  elementText: string;
  rows: ChartRow[];
};

type ClaimChartDemoProps = {
  demoMode?: boolean;
};

export default function ClaimChartDemo({ demoMode = false }: ClaimChartDemoProps) {
  const [rows, setRows] = useState<ChartRow[]>(() => loadChartRows());
  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);
  const [exportingDocx, setExportingDocx] = useState(false);

  const groupedRows = useMemo(() => groupChartRows(rows), [rows]);
  const selectedRowIdSet = useMemo(() => new Set(selectedRowIds), [selectedRowIds]);
  const selectedRowCount = selectedRowIds.length;

  useEffect(() => {
    saveChartRows(rows);
  }, [rows]);

  useEffect(() => {
    setSelectedRowIds((current) => current.filter((id) => rows.some((row) => row.id === id)));
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

  function toggleRowSelection(rowId: string) {
    setSelectedRowIds((current) =>
      current.includes(rowId) ? current.filter((id) => id !== rowId) : [...current, rowId]
    );
  }

  function toggleGroupSelection(groupId: string) {
    const group = groupedRows.find((candidate) => candidate.id === groupId);
    if (!group) {
      return;
    }

    const groupRowIds = group.rows.map((row) => row.id);
    const allSelected = groupRowIds.every((rowId) => selectedRowIdSet.has(rowId));

    setSelectedRowIds((current) => {
      if (allSelected) {
        return current.filter((id) => !groupRowIds.includes(id));
      }

      const next = new Set(current);
      for (const rowId of groupRowIds) {
        next.add(rowId);
      }
      return [...next];
    });
  }

  function selectAllRows() {
    setSelectedRowIds(rows.map((row) => row.id));
  }

  function clearSelection() {
    setSelectedRowIds([]);
  }

  function removeSelectedRows() {
    if (selectedRowIds.length === 0) {
      return;
    }

    const selectedIds = new Set(selectedRowIds);
    setRows((current) => current.filter((row) => !selectedIds.has(row.id)));
    setSelectedRowIds([]);
  }

  function updateRow(id: string, field: "notes", value: string) {
    setRows((current) => current.map((row) => (row.id === id ? { ...row, [field]: value } : row)));
  }

  function updateGroup(groupId: string, field: "claim" | "elementLabel" | "elementText", value: string) {
    setRows((current) =>
      current.map((row) => (groupIdForRow(row) === groupId ? { ...row, [field]: value } : row))
    );
  }

  function moveGroup(groupId: string, direction: "up" | "down") {
    setRows((current) => moveGroupRows(current, groupId, direction));
  }

  function moveRowWithinGroup(groupId: string, rowId: string, direction: "up" | "down") {
    setRows((current) => moveGroupEvidenceRow(current, groupId, rowId, direction));
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

  async function downloadDocx() {
    setExportingDocx(true);

    try {
      await exportClaimChartDocx(
        groupedRows.map((group) => ({
          claim: group.claim,
          elementLabel: group.elementLabel,
          elementText: group.elementText,
          rows: group.rows.map((row) => ({
            citation: row.citation,
            excerpt: row.excerpt,
            notes: row.notes,
          })),
        }))
      );
    } finally {
      setExportingDocx(false);
    }
  }

  function openRowInSearch(row: ChartRow) {
    if (!row.sourceQueryText || !row.sourceDocumentIds || row.sourceDocumentIds.length === 0) {
      return;
    }

    saveSearchNavigationTarget({
      documentIds: row.sourceDocumentIds,
      queryText: row.sourceQueryText,
      resultKey: row.sourceResultKey ?? row.id,
    });
    window.location.hash = "";
  }

  return (
    <main className={`chartDemoPage${demoMode ? " demoChartPage" : ""}`}>
      {demoMode ? (
        <section className="demoTopbar" aria-label="Claim chart workspace controls">
          <div className="demoTopbarMeta">
            <span>{rows.length} evidence row{rows.length === 1 ? "" : "s"}</span>
            <span>{groupedRows.length} group{groupedRows.length === 1 ? "" : "s"}</span>
          </div>
          <div className="demoTopbarActions">
            <a className="demoTopbarLink" href="/">
              Search workspace
            </a>
          </div>
        </section>
      ) : null}

      <section className={`panel chartDemoIntro${demoMode ? " demoChartIntro" : ""}`}>
        <div className={demoMode ? "demoPanelHeading" : undefined}>
          <div>
            <h1>Claim Chart Workspace</h1>
            <p className="subtitle">Review saved evidence, organize grouped claim rows, and keep chart drafting connected to the search workspace.</p>
          </div>
        </div>
      </section>

      <section className="chartDemoLayout">
        <div className="panel chartDemoColumn">
          <div className={demoMode ? "demoPanelHeading demoChartSectionHeader" : undefined}>
            <div>
              <h2>Saved Evidence</h2>
              <p className="subtitle">Results added from the main search page appear here and stay editable in this separate workspace.</p>
            </div>
            {demoMode ? <span className="demoResultsBadge">{rows.length} buffered</span> : null}
          </div>
          {rows.length > 0 ? (
            <div className={`chartBulkToolbar${demoMode ? " demoChartToolbar" : ""}`}>
              <span className="chartSelectionCount">{selectedRowCount} selected</span>
              <button type="button" className="chartLinkButton" onClick={selectAllRows} disabled={rows.length === 0 || selectedRowCount === rows.length}>
                Select all
              </button>
              <button type="button" className="chartLinkButton" onClick={clearSelection} disabled={selectedRowCount === 0}>
                Clear selection
              </button>
              <button type="button" className="chartActionButton chartDangerButton" onClick={removeSelectedRows} disabled={selectedRowCount === 0}>
                Remove selected
              </button>
            </div>
          ) : null}
          <div className="chartEvidenceList">
            {rows.map((item, index) => (
              <article key={item.id} className={`chartEvidenceCard${selectedRowIdSet.has(item.id) ? " chartEvidenceCardSelected" : ""}`}>
                <div className="chartEvidenceMeta">
                  <label className="chartSelectToggle">
                    <input type="checkbox" checked={selectedRowIdSet.has(item.id)} onChange={() => toggleRowSelection(item.id)} />
                    <span>Select evidence</span>
                  </label>
                  <strong>{item.reference}</strong>
                  <span>{item.location}</span>
                  <span>{item.citation}</span>
                </div>
                <p><b>Excerpt:</b> {item.excerpt}</p>
                <p><b>Why it matters:</b> {item.reason}</p>
                <div className="chartEvidenceActions">
                  <button type="button" className="chartLinkButton" onClick={() => setRows((current) => moveRow(current, index, -1))} disabled={index === 0}>
                    Move up
                  </button>
                  <button type="button" className="chartLinkButton" onClick={() => setRows((current) => moveRow(current, index, 1))} disabled={index === rows.length - 1}>
                    Move down
                  </button>
                  <button type="button" className="chartActionButton" onClick={() => openRowInSearch(item)} disabled={!item.sourceQueryText}>
                    View in search
                  </button>
                  <button type="button" className="chartActionButton" onClick={() => removeRow(item.id)}>
                    Remove from chart
                  </button>
                </div>
              </article>
            ))}
            {rows.length === 0 ? (
              <div className={`stateCard${demoMode ? " demoStateCard" : ""}`}>
                <strong className="stateCardTitle">No saved evidence yet</strong>
                <p className="stateCardText">Add passages from search results to start building a claim chart from reusable evidence.</p>
              </div>
            ) : null}
          </div>
        </div>

        <div className="panel chartDemoColumn">
          <div className={`chartWorkspaceHeader${demoMode ? " demoChartWorkspaceHeader" : ""}`}>
            <div>
              <h2>Claim Chart Workspace</h2>
              <p className="subtitle">Rows with the same claim and element label are grouped under one claim element with separate evidence entries beneath it.</p>
            </div>
            <div className={`chartHeaderActions${demoMode ? " demoChartHeaderActions" : ""}`}>
              {demoMode ? <span className="demoResultsBadge">{groupedRows.length} grouped elements</span> : null}
              <button type="button" className="chartActionButton" onClick={() => void copyChartRows()} disabled={rows.length === 0}>
                {copied ? "Copied rows" : "Copy rows as TSV"}
              </button>
              <button type="button" className="chartActionButton" onClick={() => void downloadDocx()} disabled={rows.length === 0 || exportingDocx}>
                {exportingDocx ? "Preparing DOCX" : "Download DOCX"}
              </button>
            </div>
          </div>

          <div className="chartGroupList">
            {groupedRows.map((group, groupIndex) => (
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
                  <div className="chartGroupHeaderActions">
                    <div className="chartGroupCount">{group.rows.length} evidence {group.rows.length === 1 ? "row" : "rows"}</div>
                    <div className="chartReorderActions">
                      <button
                        type="button"
                        className="chartLinkButton"
                        onClick={() => toggleGroupSelection(group.id)}
                      >
                        {group.rows.every((row) => selectedRowIdSet.has(row.id)) ? "Clear group" : "Select group"}
                      </button>
                      <button type="button" className="chartLinkButton" onClick={() => moveGroup(group.id, "up")} disabled={groupIndex === 0}>
                        Move group up
                      </button>
                      <button
                        type="button"
                        className="chartLinkButton"
                        onClick={() => moveGroup(group.id, "down")}
                        disabled={groupIndex === groupedRows.length - 1}
                      >
                        Move group down
                      </button>
                    </div>
                  </div>
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
                  {group.rows.map((row, rowIndex) => (
                    <article key={row.id} className={`chartGroupEvidenceCard${selectedRowIdSet.has(row.id) ? " chartGroupEvidenceCardSelected" : ""}`}>
                      <details className={`chartEvidenceDisclosure${demoMode ? " demoDisclosureUtility" : ""}`}>
                        <summary className={`chartEvidenceSummary${demoMode ? " demoDisclosureSummary demoDisclosureSummaryUtility" : ""}`}>
                          <label
                            className="chartSelectToggle chartEvidenceSelectToggle"
                            onClick={(event) => event.preventDefault()}
                          >
                            <input
                              type="checkbox"
                              checked={selectedRowIdSet.has(row.id)}
                              onChange={() => toggleRowSelection(row.id)}
                            />
                            <span>Select evidence</span>
                          </label>
                          <div className="chartGroupEvidenceMeta">
                            <strong>{row.citation}</strong>
                            <span>{row.reference}</span>
                          </div>
                          <p className="chartEvidencePreview">{previewExcerpt(row.excerpt)}</p>
                        </summary>

                        <div className={`chartEvidenceDetail${demoMode ? " demoContextBlock" : ""}`}>
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
                          <div className="chartEvidenceActions">
                            <button
                              type="button"
                              className="chartLinkButton"
                              onClick={() => moveRowWithinGroup(group.id, row.id, "up")}
                              disabled={rowIndex === 0}
                            >
                              Move up
                            </button>
                            <button
                              type="button"
                              className="chartLinkButton"
                              onClick={() => moveRowWithinGroup(group.id, row.id, "down")}
                              disabled={rowIndex === group.rows.length - 1}
                            >
                              Move down
                            </button>
                            <button type="button" className="chartLinkButton" onClick={() => openRowInSearch(row)} disabled={!row.sourceQueryText}>
                              View in search
                            </button>
                            <button type="button" className="chartLinkButton" onClick={() => removeRow(row.id)}>
                              Remove evidence
                            </button>
                          </div>
                        </div>
                      </details>
                    </article>
                  ))}
                </div>
              </section>
            ))}
          </div>

          {rows.length === 0 ? (
            <div className={`stateCard${demoMode ? " demoStateCard" : ""}`}>
              <strong className="stateCardTitle">Chart workspace empty</strong>
              <p className="stateCardText">Once evidence is saved on the left, grouped claim elements will appear here for editing and export.</p>
            </div>
          ) : null}
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

function moveRow(rows: ChartRow[], index: number, delta: -1 | 1) {
  const targetIndex = index + delta;
  if (index < 0 || index >= rows.length || targetIndex < 0 || targetIndex >= rows.length) {
    return rows;
  }

  const nextRows = [...rows];
  const [row] = nextRows.splice(index, 1);
  nextRows.splice(targetIndex, 0, row);
  return nextRows;
}

function moveGroupRows(rows: ChartRow[], groupId: string, direction: "up" | "down") {
  const groups = groupChartRows(rows);
  const groupIndex = groups.findIndex((group) => group.id === groupId);
  if (groupIndex === -1) {
    return rows;
  }

  const targetIndex = direction === "up" ? groupIndex - 1 : groupIndex + 1;
  if (targetIndex < 0 || targetIndex >= groups.length) {
    return rows;
  }

  const orderedGroups = [...groups];
  const [group] = orderedGroups.splice(groupIndex, 1);
  orderedGroups.splice(targetIndex, 0, group);

  return orderedGroups.flatMap((orderedGroup) => orderedGroup.rows);
}

function moveGroupEvidenceRow(rows: ChartRow[], groupId: string, rowId: string, direction: "up" | "down") {
  const groups = groupChartRows(rows);
  const groupIndex = groups.findIndex((group) => group.id === groupId);
  if (groupIndex === -1) {
    return rows;
  }

  const group = groups[groupIndex];
  const rowIndex = group.rows.findIndex((row) => row.id === rowId);
  if (rowIndex === -1) {
    return rows;
  }

  const targetIndex = direction === "up" ? rowIndex - 1 : rowIndex + 1;
  if (targetIndex < 0 || targetIndex >= group.rows.length) {
    return rows;
  }

  const reorderedGroupRows = moveRow(group.rows, rowIndex, direction === "up" ? -1 : 1);
  return groups.flatMap((candidateGroup) => (candidateGroup.id === groupId ? reorderedGroupRows : candidateGroup.rows));
}