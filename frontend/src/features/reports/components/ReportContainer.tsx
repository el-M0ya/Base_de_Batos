import { ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../../../shared/auth/useAuth';
import { Alert } from '../../../shared/components/Alert';
import { EmptyState } from '../../../shared/components/EmptyState';
import { messages } from '../../../shared/i18n/messages';
import { findReport } from '../reportsRegistry';
import { ReportView } from './ReportView';
import styles from './ReportView.module.css';

const t = messages.reports.detail;

/**
 * Report detail page (`/reports/:id`): finds the report in the registry,
 * checks the user's role and renders the shared `ReportView`.
 *
 * @remarks
 * This is where each report will load its data with its own hook (filters,
 * query, state) once the backend exposes the query. Until then every report
 * renders as "coming soon".
 */
export function ReportContainer() {
  const { id } = useParams();
  const { user } = useAuth();
  const report = findReport(id);

  if (report === undefined) {
    return (
      <section className={styles.page}>
        <BackLink />
        <EmptyState title={t.notFoundTitle} description={t.notFoundDescription} />
      </section>
    );
  }

  if (user === null || !report.roles.includes(user.role)) {
    return (
      <section className={styles.page}>
        <BackLink />
        <Alert>{messages.auth.notAuthorized}</Alert>
      </section>
    );
  }

  return <ReportView report={report} state="coming-soon" />;
}

/** Link back to the reports catalog. */
function BackLink() {
  return (
    <Link to="/reports" className={styles.back}>
      <ArrowLeft size={16} aria-hidden="true" />
      {t.back}
    </Link>
  );
}
