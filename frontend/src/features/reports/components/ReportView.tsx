import type { ReactNode } from 'react';
import { ArrowLeft, Clock, SearchX } from 'lucide-react';
import { Link } from 'react-router-dom';
import { EmptyState } from '../../../shared/components/EmptyState';
import { ErrorState } from '../../../shared/components/ErrorState';
import { ExportPdfButton } from '../../../shared/components/ExportPdfButton';
import { LoadingState } from '../../../shared/components/LoadingState';
import type { PdfExportOptions } from '../../../shared/export/exportToPdf';
import { messages } from '../../../shared/i18n/messages';
import type { ReportDefinition } from '../reportsRegistry';
import styles from './ReportView.module.css';

const t = messages.reports.detail;

/**
 * What the report body shows:
 * - `coming-soon`: the backend query does not exist yet;
 * - `loading` / `error`: fetching the data, or it failed;
 * - `empty`: the filters returned no rows;
 * - `insufficient`: there are rows, but too few for a meaningful analysis;
 * - `ready`: the results (`children`).
 */
export type ReportViewState =
  'coming-soon' | 'loading' | 'error' | 'empty' | 'insufficient' | 'ready';

/** Props of the report view. */
export interface ReportViewProps {
  /** Report from the registry (code, title, requirements...). */
  report: ReportDefinition;
  /** What the body shows. */
  state: ReportViewState;
  /** Report filters, shown above the results. */
  filters?: ReactNode;
  /** What to export; the PDF button only appears with results. */
  getExport?: () => PdfExportOptions;
  /** Retries loading after an error. */
  onRetry?: () => void;
  /** Results, usually one or more `ReportSectionPanel`. */
  children?: ReactNode;
}

/**
 * Presentational skeleton shared by the six reports: header, filters,
 * export button and the body for the current state. It has no data logic.
 */
export function ReportView({
  report,
  state,
  filters,
  getExport,
  onRetry,
  children,
}: ReportViewProps) {
  return (
    <section className={styles.page} aria-labelledby="report-title">
      <Link to="/reports" className={styles.back}>
        <ArrowLeft size={16} aria-hidden="true" />
        {t.back}
      </Link>

      <header className={styles.header}>
        <div>
          <div className={styles.codes}>
            <span className={styles.code}>{report.code}</span>
            {report.requirements.map((requirement) => (
              <span key={requirement} className={styles.badge}>
                {requirement}
              </span>
            ))}
          </div>
          <h1 id="report-title" className={styles.title}>
            {report.title}
          </h1>
          <p className={styles.description}>{report.description}</p>
        </div>
        {state === 'ready' && getExport !== undefined && <ExportPdfButton getExport={getExport} />}
      </header>

      {state !== 'coming-soon' && filters !== undefined && (
        <div className={styles.filters}>{filters}</div>
      )}

      <ReportBody state={state} onRetry={onRetry}>
        {children}
      </ReportBody>
    </section>
  );
}

/** Body of the report for each state. */
function ReportBody({
  state,
  onRetry,
  children,
}: {
  state: ReportViewState;
  onRetry: (() => void) | undefined;
  children: ReactNode;
}) {
  switch (state) {
    case 'coming-soon':
      return (
        <EmptyState
          icon={<Clock size={28} />}
          title={messages.comingSoon.title}
          description={t.comingSoonDescription}
        />
      );
    case 'loading':
      return <LoadingState />;
    case 'error':
      return <ErrorState onRetry={onRetry} />;
    case 'empty':
      return (
        <EmptyState
          icon={<SearchX size={28} />}
          title={t.emptyTitle}
          description={t.emptyDescription}
        />
      );
    case 'insufficient':
      return <EmptyState title={t.insufficientTitle} description={t.insufficientDescription} />;
    case 'ready':
      return <div className={styles.results}>{children}</div>;
  }
}
