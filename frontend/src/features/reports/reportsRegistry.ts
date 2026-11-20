/**
 * Central catalog of the six system reports (REP-01 to REP-06).
 *
 * @remarks
 * Single source for every report's identifier, title, route, allowed roles and
 * covered requirements: the reports page, the routes and future navigation all
 * read from here. While the backend queries do not exist, every report is
 * `coming-soon`; switching one to `available` enables its link.
 *
 * Allowed roles are not defined by the requirements; the current split is a
 * documented assumption (see `docs/frontend/reports.md`).
 */
import {
  ArrowLeftRight,
  ChartColumnStacked,
  ClipboardList,
  Dumbbell,
  ShieldCheck,
  TrendingUp,
  type LucideIcon,
} from 'lucide-react';
import { messages } from '../../shared/i18n/messages';
import type { UserRole } from '../../shared/types/roles';

const t = messages.reports.items;

/** Whether a report can already be opened. */
export type ReportStatus = 'available' | 'coming-soon';

/** One result group of a report that combines several queries (REP-06). */
export interface ReportSection {
  /** Functional requirement covered by the section, e.g. "RF-41". */
  requirement: string;
  /** Section title shown on the card and in the report. */
  title: string;
}

/** Definition of one report in the catalog. */
export interface ReportDefinition {
  /** URL-safe identifier, e.g. "rep-03". */
  id: string;
  /** Requirement code shown to the user, e.g. "REP-03". */
  code: string;
  /** Report title. */
  title: string;
  /** Short description of what the report shows. */
  description: string;
  /** Functional requirements covered, e.g. ["RF-37"]. */
  requirements: string[];
  /** Roles allowed to see the report. */
  roles: UserRole[];
  /** Whether the report can be opened yet. */
  status: ReportStatus;
  /** Icon shown on the report card. */
  icon: LucideIcon;
  /** Result groups, only for reports that combine several queries. */
  sections?: ReportSection[];
}

/** Staff roles: reports about routines, programs and validations. */
const STAFF: UserRole[] = ['administrator', 'trainer'];

/** The six reports, in requirement order. */
export const reports: ReportDefinition[] = [
  {
    id: 'rep-01',
    code: 'REP-01',
    ...t.rep01,
    requirements: ['RF-35'],
    roles: STAFF,
    status: 'coming-soon',
    icon: ClipboardList,
  },
  {
    id: 'rep-02',
    code: 'REP-02',
    ...t.rep02,
    requirements: ['RF-36'],
    roles: STAFF,
    status: 'coming-soon',
    icon: Dumbbell,
  },
  {
    id: 'rep-03',
    code: 'REP-03',
    ...t.rep03,
    requirements: ['RF-37'],
    roles: STAFF,
    status: 'coming-soon',
    icon: ShieldCheck,
  },
  {
    id: 'rep-04',
    code: 'REP-04',
    ...t.rep04,
    requirements: ['RF-38'],
    // Clients may consult their own progress reports (functional requirements).
    roles: [...STAFF, 'client'],
    status: 'coming-soon',
    icon: TrendingUp,
  },
  {
    id: 'rep-05',
    code: 'REP-05',
    ...t.rep05,
    requirements: ['RF-39'],
    roles: STAFF,
    status: 'coming-soon',
    icon: ArrowLeftRight,
  },
  {
    id: 'rep-06',
    code: 'REP-06',
    title: t.rep06.title,
    description: t.rep06.description,
    requirements: ['RF-40', 'RF-41', 'RF-42'],
    roles: STAFF,
    status: 'coming-soon',
    icon: ChartColumnStacked,
    sections: [
      { requirement: 'RF-40', title: t.rep06.sections.correlation },
      { requirement: 'RF-41', title: t.rep06.sections.abandonment },
      { requirement: 'RF-42', title: t.rep06.sections.adjustments },
    ],
  },
];

/** Route of a report's detail page, e.g. "/reports/rep-03". */
export function reportPath(report: ReportDefinition): string {
  return `/reports/${report.id}`;
}

/** Reports the given role may see; none when there is no session. */
export function reportsForRole(role: UserRole | undefined): ReportDefinition[] {
  if (role === undefined) return [];
  return reports.filter((report) => report.roles.includes(role));
}

/** Finds a report by its identifier. */
export function findReport(id: string | undefined): ReportDefinition | undefined {
  return reports.find((report) => report.id === id);
}
