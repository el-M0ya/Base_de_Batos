import { describe, expect, it } from 'vitest';
import { filterReports } from './filterReports';
import { reports, type ReportDefinition } from './reportsRegistry';

const codes = (list: ReportDefinition[]) => list.map((report) => report.code);

describe('filterReports', () => {
  it('returns every report with an empty search on the "all" tab', () => {
    expect(filterReports(reports, '', 'all')).toHaveLength(6);
  });

  it('searches titles ignoring accents and case', () => {
    expect(codes(filterReports(reports, 'ANALISIS', 'all'))).toEqual(['REP-06']);
  });

  it('searches report codes, requirements and section titles', () => {
    expect(codes(filterReports(reports, 'rep-03', 'all'))).toEqual(['REP-03']);
    expect(codes(filterReports(reports, 'RF-41', 'all'))).toEqual(['REP-06']);
    expect(codes(filterReports(reports, 'abandono', 'all'))).toEqual(['REP-06']);
  });

  it('requires every search word to match', () => {
    expect(codes(filterReports(reports, 'rutinas validadas', 'all'))).toEqual(['REP-03']);
  });

  it('filters by status tab', () => {
    expect(filterReports(reports, '', 'coming-soon')).toHaveLength(6);
    expect(filterReports(reports, '', 'available')).toEqual([]);
  });
});
