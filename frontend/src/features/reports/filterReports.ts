import type { ReportDefinition, ReportStatus } from './reportsRegistry';

/** Status tab of the reports page: every report or only one status. */
export type ReportTab = 'all' | ReportStatus;

/** Lower-cases a text and removes accents, so "analisis" finds "Análisis". */
function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
}

/** All the texts of a report the search looks into. */
function searchableText(report: ReportDefinition): string {
  const sections = report.sections?.map((section) => section.title) ?? [];
  return normalize(
    [report.code, report.title, report.description, ...report.requirements, ...sections].join(' '),
  );
}

/**
 * Keeps the reports that match the search text and the selected tab.
 *
 * @param list - Reports visible to the user.
 * @param query - Search text; empty means no text filter.
 * @param tab - Status tab.
 */
export function filterReports(
  list: ReportDefinition[],
  query: string,
  tab: ReportTab,
): ReportDefinition[] {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  return list.filter((report) => {
    if (tab !== 'all' && report.status !== tab) return false;
    const text = searchableText(report);
    return words.every((word) => text.includes(word));
  });
}
