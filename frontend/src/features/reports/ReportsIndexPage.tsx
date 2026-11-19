import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { useAuth } from '../../shared/auth/useAuth';
import { EmptyState } from '../../shared/components/EmptyState';
import { messages } from '../../shared/i18n/messages';
import { ReportCard } from './ReportCard';
import { filterReports, type ReportTab } from './filterReports';
import { reportsForRole } from './reportsRegistry';
import styles from './ReportsIndexPage.module.css';

const t = messages.reports;

/**
 * Reports catalog: the reports the user's role may see, with a text search
 * and status tabs (all / available / coming soon).
 */
export function ReportsIndexPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState<ReportTab>('all');

  const visible = useMemo(() => reportsForRole(user?.role), [user?.role]);
  const shown = filterReports(visible, query, tab);

  // Tab counters follow the search text, so they always match what each tab shows.
  const tabs: { id: ReportTab; label: string }[] = [
    { id: 'all', label: t.tabs.all(filterReports(visible, query, 'all').length) },
    {
      id: 'available',
      label: t.tabs.available(filterReports(visible, query, 'available').length),
    },
    {
      id: 'coming-soon',
      label: t.tabs.comingSoon(filterReports(visible, query, 'coming-soon').length),
    },
  ];

  return (
    <section className={styles.page} aria-labelledby="reports-title">
      <header className={styles.header}>
        <div>
          <h1 id="reports-title" className={styles.title}>
            {t.title}
          </h1>
          <p className={styles.subtitle}>{t.subtitle}</p>
        </div>
        <p className={styles.summary}>{t.summary(visible.length)}</p>
      </header>

      <div className={styles.toolbar}>
        <label className={styles.search}>
          <Search size={18} aria-hidden="true" />
          <input
            type="search"
            aria-label={t.searchLabel}
            placeholder={t.searchPlaceholder}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <div className={styles.tabs} role="group" aria-label={t.filtersLabel}>
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              className={styles.tab}
              aria-pressed={tab === item.id}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {shown.length === 0 ? (
        <EmptyState title={t.noResults} description={t.noResultsHint} />
      ) : (
        <div className={styles.grid}>
          {shown.map((report) => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </section>
  );
}
