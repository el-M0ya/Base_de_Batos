/**
 * Draws a table into a PDF document and downloads it.
 *
 * @remarks
 * jsPDF and its table plugin are heavy, so they are loaded with a dynamic
 * `import()` only when the user actually exports: they never slow down the
 * first page load. The table content comes from `buildPdfTable`.
 */
import { messages } from '../i18n/messages';
import type { PdfTableData } from './buildPdfTable';

/** Options for one PDF export. */
export interface PdfExportOptions {
  /** Document title, like the page or report name. */
  title: string;
  /** Base file name without extension; the date is appended. */
  fileName: string;
  /** Table content built with `buildPdfTable`. */
  table: PdfTableData;
  /** Optional line under the title, e.g. the active filters. */
  subtitle?: string;
}

/** Page margin, in millimetres. */
const MARGIN = 14;

/** Brand colour (FORJA primary, #8a4bff) for the table header. */
const HEADER_COLOR: [number, number, number] = [138, 75, 255];

/** Pads a number to two digits ("5" → "05"). */
function pad(value: number): string {
  return String(value).padStart(2, '0');
}

/** Formats a date as "15/11/2026 09:05" (local time). */
export function formatGeneratedDate(date: Date): string {
  return (
    `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

/** Builds the file name, e.g. "ejercicios-2026-11-15.pdf" (local date). */
export function pdfFileName(base: string, date: Date): string {
  return `${base}-${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}.pdf`;
}

/**
 * Generates the PDF (title, optional subtitle, generation date and table)
 * and triggers the download.
 *
 * @param options - What to export.
 * @param now - Generation date; tests pass a fixed one.
 */
export async function exportToPdf(options: PdfExportOptions, now = new Date()): Promise<void> {
  const [{ jsPDF }, { default: autoTable }] = await Promise.all([
    import('jspdf'),
    import('jspdf-autotable'),
  ]);

  // Landscape: report tables usually have many columns.
  const doc = new jsPDF({ orientation: 'landscape' });
  let y = 16;

  doc.setFontSize(16);
  doc.text(options.title, MARGIN, y);

  doc.setFontSize(10);
  if (options.subtitle !== undefined && options.subtitle !== '') {
    y += 7;
    doc.text(options.subtitle, MARGIN, y);
  }
  y += 6;
  doc.setTextColor(110);
  doc.text(messages.pdfExport.generatedOn(formatGeneratedDate(now)), MARGIN, y);
  doc.setTextColor(0);

  autoTable(doc, {
    head: [options.table.head],
    body: options.table.body,
    startY: y + 6,
    margin: { left: MARGIN, right: MARGIN },
    styles: { fontSize: 9 },
    headStyles: { fillColor: HEADER_COLOR, textColor: 255 },
  });

  doc.save(pdfFileName(options.fileName, now));
}
