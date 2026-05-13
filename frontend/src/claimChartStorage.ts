export const CLAIM_CHART_STORAGE_KEY = "claim-chart-rows";

export type ChartRow = {
  id: string;
  claim: string;
  elementLabel: string;
  reference: string;
  location: string;
  citation: string;
  excerpt: string;
  reason: string;
  elementText: string;
  notes: string;
};

type StoredChartRow = Partial<ChartRow> & { id?: unknown };

export function loadChartRows(): ChartRow[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(CLAIM_CHART_STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(normalizeChartRow).filter((row): row is ChartRow => row !== null) : [];
  } catch {
    return [];
  }
}

export function saveChartRows(rows: ChartRow[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(CLAIM_CHART_STORAGE_KEY, JSON.stringify(rows));
}

export function upsertChartRow(row: ChartRow) {
  const existingRows = loadChartRows();
  const alreadyExists = existingRows.some((existingRow) => existingRow.id === row.id);
  const nextRows = alreadyExists
    ? existingRows.map((existingRow) => (existingRow.id === row.id ? row : existingRow))
    : [...existingRows, row];

  saveChartRows(nextRows);
  return alreadyExists;
}

function normalizeChartRow(row: StoredChartRow, index: number): ChartRow | null {
  if (!row || typeof row !== "object") {
    return null;
  }

  const reference = typeof row.reference === "string" ? row.reference : "";
  const location = typeof row.location === "string" ? row.location : "";

  return {
    id: typeof row.id === "string" ? row.id : `chart-row-${index}`,
    claim: typeof row.claim === "string" ? row.claim : "Claim ?",
    elementLabel: typeof row.elementLabel === "string" ? row.elementLabel : "",
    reference,
    location,
    citation:
      typeof row.citation === "string" && row.citation.trim().length > 0
        ? row.citation
        : [reference, location].filter(Boolean).join(", "),
    excerpt: typeof row.excerpt === "string" ? row.excerpt : "",
    reason: typeof row.reason === "string" ? row.reason : "",
    elementText: typeof row.elementText === "string" ? row.elementText : "",
    notes: typeof row.notes === "string" ? row.notes : "",
  };
}