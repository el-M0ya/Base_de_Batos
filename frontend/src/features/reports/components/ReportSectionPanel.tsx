import { DataTable } from '../../../shared/components/DataTable/DataTable';
import type { ColumnDef, SortDirection } from '../../../shared/components/DataTable/columns';
import { ChartPanel, type ChartPanelProps } from './ChartPanel';
import styles from './ReportView.module.css';

/** Props of one "chart + table" block of a report. */
export interface ReportSectionPanelProps<T extends object> {
  /** Section title; only reports with several sections (REP-06) need it. */
  title?: string;
  /** Requirement covered by the section, e.g. "RF-41". */
  requirement?: string;
  /** Optional chart drawn above the table. */
  chart?: ChartPanelProps;
  /** Table columns (also used for the PDF). */
  columns: ColumnDef<T>[];
  /** Rows to show. */
  rows: T[];
  /** Accessible label of the table. */
  tableLabel: string;
  /** Notifies the active sort, so the PDF can keep the same order. */
  onSortChange?: ((accessor: keyof T | null, direction: SortDirection) => void) | undefined;
}

/**
 * One result block of a report: optional chart plus sortable table (RF-43).
 * A report with several queries (REP-06) renders one block per query.
 */
export function ReportSectionPanel<T extends object>({
  title,
  requirement,
  chart,
  columns,
  rows,
  tableLabel,
  onSortChange,
}: ReportSectionPanelProps<T>) {
  return (
    <section className={styles.section}>
      {title !== undefined && (
        <h2 className={styles.sectionTitle}>
          {title}
          {requirement !== undefined && <span className={styles.badge}>{requirement}</span>}
        </h2>
      )}
      {chart !== undefined && <ChartPanel {...chart} />}
      <DataTable columns={columns} data={rows} ariaLabel={tableLabel} onSortChange={onSortChange} />
    </section>
  );
}
