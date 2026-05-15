import {
  AlignmentType,
  BorderStyle,
  Document,
  HeadingLevel,
  PageOrientation,
  Packer,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableLayoutType,
  TableRow,
  TextRun,
  VerticalAlign,
  WidthType,
} from "docx";

type ExportEvidenceRow = {
  citation: string;
  excerpt: string;
  notes: string;
};

export type ExportClaimElementGroup = {
  claim: string;
  elementLabel: string;
  elementText: string;
  rows: ExportEvidenceRow[];
};

const LETTER_SHORT_EDGE_TWIPS = 12240;
const LETTER_LONG_EDGE_TWIPS = 15840;
const PAGE_MARGIN_TWIPS = 720;
const TABLE_WIDTH_TWIPS = LETTER_LONG_EDGE_TWIPS - PAGE_MARGIN_TWIPS * 2;
const COLUMN_WIDTHS_TWIPS = [2880, 5760, 5760] as const;
const CELL_MARGIN_TWIPS = 120;
const TABLE_BORDER = { style: BorderStyle.SINGLE, size: 6, color: "B8C1CC" };
const HEADER_SHADING = { type: ShadingType.CLEAR, fill: "E8EEF6", color: "auto" };

export async function exportClaimChartDocx(groups: ExportClaimElementGroup[]) {
  const document = new Document({
    sections: [
      {
        properties: {
          page: {
            size: {
              width: LETTER_SHORT_EDGE_TWIPS,
              height: LETTER_LONG_EDGE_TWIPS,
              orientation: PageOrientation.LANDSCAPE,
            },
            margin: {
              top: PAGE_MARGIN_TWIPS,
              right: PAGE_MARGIN_TWIPS,
              bottom: PAGE_MARGIN_TWIPS,
              left: PAGE_MARGIN_TWIPS,
            },
          },
        },
        children: buildDocumentChildren(groups),
      },
    ],
  });

  const blob = await Packer.toBlob(document);
  const url = URL.createObjectURL(blob);
  const link = window.document.createElement("a");
  link.href = url;
  link.download = "claim-chart-demo.docx";
  link.click();
  URL.revokeObjectURL(url);
}

function buildDocumentChildren(groups: ExportClaimElementGroup[]) {
  const generatedAt = new Date().toLocaleString();

  return [
    new Paragraph({
      text: "Claim Chart Demo Export",
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.CENTER,
      spacing: { after: 240 },
    }),
    new Paragraph({
      children: [new TextRun({ text: `Generated: ${generatedAt}`, italics: true })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 320 },
    }),
    ...groups.flatMap((group, index) => buildGroupSection(group, index)),
  ];
}

function buildGroupSection(group: ExportClaimElementGroup, index: number) {
  const claimText = group.claim.trim() || `Claim Group ${index + 1}`;
  const elementLabel = group.elementLabel.trim() || `Element ${index + 1}`;
  const elementText = group.elementText.trim() || "(claim element text not filled)";

  return [
    new Paragraph({
      text: `${claimText} - ${elementLabel}`,
      heading: HeadingLevel.HEADING_1,
      spacing: { before: index === 0 ? 0 : 240, after: 120 },
    }),
    new Paragraph({
      children: [
        new TextRun({ text: "Claim element: ", bold: true }),
        new TextRun({ text: elementText }),
      ],
      spacing: { after: 180 },
    }),
    new Table({
      width: { size: TABLE_WIDTH_TWIPS, type: WidthType.DXA },
      columnWidths: COLUMN_WIDTHS_TWIPS,
      layout: TableLayoutType.FIXED,
      margins: {
        top: CELL_MARGIN_TWIPS,
        right: CELL_MARGIN_TWIPS,
        bottom: CELL_MARGIN_TWIPS,
        left: CELL_MARGIN_TWIPS,
      },
      borders: {
        top: TABLE_BORDER,
        right: TABLE_BORDER,
        bottom: TABLE_BORDER,
        left: TABLE_BORDER,
        insideHorizontal: TABLE_BORDER,
        insideVertical: TABLE_BORDER,
      },
      tableLook: {
        firstRow: true,
        noHBand: true,
        noVBand: true,
      },
      rows: [buildHeaderRow(), ...group.rows.map((row) => buildEvidenceRow(row))],
    }),
    new Paragraph({ spacing: { after: 160 } }),
  ];
}

function buildHeaderRow() {
  return new TableRow({
    tableHeader: true,
    children: [
      buildCell("Citation", 0, true),
      buildCell("Excerpt", 1, true),
      buildCell("Analysis", 2, true),
    ],
  });
}

function buildEvidenceRow(row: ExportEvidenceRow) {
  return new TableRow({
    children: [
      buildCell(row.citation || "(citation missing)", 0),
      buildCell(row.excerpt || "(excerpt missing)", 1),
      buildCell(row.notes || "(analysis missing)", 2),
    ],
  });
}

function buildCell(text: string, columnIndex: number, bold = false) {
  return new TableCell({
    width: { size: COLUMN_WIDTHS_TWIPS[columnIndex], type: WidthType.DXA },
    verticalAlign: VerticalAlign.TOP,
    shading: bold ? HEADER_SHADING : undefined,
    children: [
      new Paragraph({
        children: buildTextRuns(text, bold),
        wordWrap: true,
        spacing: { before: 0, after: 0 },
      }),
    ],
  });
}

function buildTextRuns(text: string, bold: boolean) {
  const normalizedText = text.replace(/\t/g, " ").replace(/\r\n?/g, "\n");
  const lines = normalizedText.split("\n");

  return lines.map(
    (line, index) =>
      new TextRun({
        text: line,
        bold,
        break: index === 0 ? undefined : 1,
        size: bold ? 20 : 18,
        font: "Arial",
      })
  );
}
