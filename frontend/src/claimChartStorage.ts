export const CLAIM_CHART_STORAGE_KEY = "claim-chart-rows";

export type ChartRow = {
  id: string;
  claim: string;
  reference: string;
  location: string;
  excerpt: string;
  reason: string;
  elementText: string;
  notes: string;
};

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
    return Array.isArray(parsed) ? parsed : [];
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