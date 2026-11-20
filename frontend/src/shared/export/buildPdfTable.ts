/**
 * Turns table columns and rows into plain text ready to be drawn in a PDF.
 *
 * @remarks
 * Pure function: it does not filter, sort or touch the PDF library. The caller
 * passes the rows exactly as the user sees them (already filtered and sorted),
 * and the same `ColumnDef` list used by `DataTable`, so headers and formatting
 * match the screen.
 */
import type { ColumnDef } from '../components/DataTable/columns';
import { messages } from '../i18n/messages';

/** Table content for the PDF: plain text only. */
export interface PdfTableData {
  /** Column headers, in display order. */
  head: string[];
  /** One array of cell texts per row, in the order received. */
  body: string[][];
}

/**
 * Returns the text of one cell, as the table shows it.
 * Empty values become the shared empty marker.
 */
function cellText<T>(column: ColumnDef<T>, row: T): string {
  const value = row[column.accessor];
  if (column.format !== undefined) {
    return column.format(value);
  }
  if (value === null || value === undefined || value === '') {
    return messages.common.emptyValue;
  }
  return String(value);
}

/**
 * Builds the PDF table content from the visible columns and rows.
 *
 * @param columns - Column definitions; those with `exportable: false` are skipped.
 * @param rows - Rows to export, already filtered and sorted by the caller.
 */
export function buildPdfTable<T>(columns: ColumnDef<T>[], rows: T[]): PdfTableData {
  const exportable = columns.filter((column) => column.exportable !== false);
  return {
    head: exportable.map((column) => column.header),
    body: rows.map((row) => exportable.map((column) => cellText(column, row))),
  };
}
