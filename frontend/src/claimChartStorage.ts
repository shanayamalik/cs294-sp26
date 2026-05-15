export const CLAIM_CHART_STORAGE_KEY = "claim-chart-rows";
export const SEARCH_NAVIGATION_STORAGE_KEY = "claim-chart-search-navigation";

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
  sourceDocumentIds?: string[];
  sourceQueryText?: string;
  sourceResultKey?: string;
};

export type SearchNavigationTarget = {
  documentIds: string[];
  queryText: string;
  resultKey: string;
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

export function saveSearchNavigationTarget(target: SearchNavigationTarget) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(SEARCH_NAVIGATION_STORAGE_KEY, JSON.stringify(target));
}

export function loadSearchNavigationTarget(): SearchNavigationTarget | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(SEARCH_NAVIGATION_STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }

    const documentIds = Array.isArray(parsed.documentIds)
      ? parsed.documentIds.filter((value: unknown): value is string => typeof value === "string" && value.trim().length > 0)
      : [];
    const queryText = typeof parsed.queryText === "string" ? parsed.queryText : "";
    const resultKey = typeof parsed.resultKey === "string" ? parsed.resultKey : "";

    if (documentIds.length === 0 || !queryText.trim() || !resultKey.trim()) {
      return null;
    }

    return { documentIds, queryText, resultKey };
  } catch {
    return null;
  }
}

export function clearSearchNavigationTarget() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(SEARCH_NAVIGATION_STORAGE_KEY);
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
    sourceDocumentIds: Array.isArray(row.sourceDocumentIds)
      ? row.sourceDocumentIds.filter((value): value is string => typeof value === "string" && value.trim().length > 0)
      : undefined,
    sourceQueryText: typeof row.sourceQueryText === "string" ? row.sourceQueryText : undefined,
    sourceResultKey: typeof row.sourceResultKey === "string" ? row.sourceResultKey : undefined,
  };
}