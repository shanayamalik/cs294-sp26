import {
  AlignmentType,
  Document,
  HeadingLevel,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableLayoutType,
  TableRow,
  TextRun,
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

export async function exportClaimChartDocx(groups: ExportClaimElementGroup[]) {
  const document = new Document({
    sections: [
      {
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
      width: { size: 100, type: WidthType.PERCENTAGE },
      layout: TableLayoutType.FIXED,
      rows: [buildHeaderRow(), ...group.rows.map((row) => buildEvidenceRow(row))],
    }),
  ];
}

function buildHeaderRow() {
  return new TableRow({
    tableHeader: true,
    children: [
      buildCell("Citation", true, 24),
      buildCell("Excerpt", true, 38),
      buildCell("Analysis", true, 38),
    ],
  });
}

function buildEvidenceRow(row: ExportEvidenceRow) {
  return new TableRow({
    children: [
      buildCell(row.citation || "(citation missing)", false, 24),
      buildCell(row.excerpt || "(excerpt missing)", false, 38),
      buildCell(row.notes || "(analysis missing)", false, 38),
    ],
  });
}

function buildCell(text: string, bold: boolean, widthPercent: number) {
  return new TableCell({
    width: { size: widthPercent, type: WidthType.PERCENTAGE },
    children: [
      new Paragraph({
        children: [new TextRun({ text, bold })],
      }),
    ],
  });
}