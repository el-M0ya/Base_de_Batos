import { ArrowRight, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { messages } from '../../shared/i18n/messages';
import { reportPath, type ReportDefinition } from './reportsRegistry';
import styles from './ReportCard.module.css';

const t = messages.reports;

/** Props of a report card. */
export interface ReportCardProps {
  /** Report to show. */
  report: ReportDefinition;
}

/**
 * Card of one report in the catalog: code, requirements, title, description,
 * sections (REP-06) and either a link to the report or a "coming soon" badge.
 */
export function ReportCard({ report }: ReportCardProps) {
  const Icon = report.icon;
  const titleId = `${report.id}-title`;

  return (
    <article className={styles.card} aria-labelledby={titleId}>
      <div className={styles.top}>
        <span className={styles.icon} aria-hidden="true">
          <Icon size={22} />
        </span>
        <div className={styles.codes}>
          <span className={styles.code}>{report.code}</span>
          {report.sections === undefined &&
            report.requirements.map((requirement) => (
              <span key={requirement} className={styles.requirement}>
                {requirement}
              </span>
            ))}
        </div>
      </div>

      <h2 id={titleId} className={styles.title}>
        {report.title}
      </h2>
      <p className={styles.description}>{report.description}</p>

      {report.sections !== undefined && (
        <ul className={styles.sections} aria-label={t.sectionsLabel}>
          {report.sections.map((section) => (
            <li key={section.requirement}>
              <span>{section.title}</span>
              <span className={styles.requirement}>{section.requirement}</span>
            </li>
          ))}
        </ul>
      )}

      <div className={styles.footer}>
        {report.status === 'available' ? (
          <Link to={reportPath(report)} className={styles.link}>
            {t.viewReport}
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
        ) : (
          <span className={styles.comingSoon}>
            <Clock size={14} aria-hidden="true" />
            {t.status.comingSoon}
          </span>
        )}
      </div>
    </article>
  );
}
