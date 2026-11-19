import { describe, expect, it } from 'vitest';
import { findReport, reportPath, reports, reportsForRole } from './reportsRegistry';

describe('reportsRegistry', () => {
  it('declares the six reports with their functional requirements', () => {
    expect(reports.map((report) => [report.code, report.requirements])).toEqual([
      ['REP-01', ['RF-35']],
      ['REP-02', ['RF-36']],
      ['REP-03', ['RF-37']],
      ['REP-04', ['RF-38']],
      ['REP-05', ['RF-39']],
      ['REP-06', ['RF-40', 'RF-41', 'RF-42']],
    ]);
  });

  it('splits REP-06 into its three sections', () => {
    expect(findReport('rep-06')?.sections?.map((section) => section.requirement)).toEqual([
      'RF-40',
      'RF-41',
      'RF-42',
    ]);
  });

  it('marks every report as coming soon until the backend queries exist', () => {
    expect(reports.every((report) => report.status === 'coming-soon')).toBe(true);
  });

  it('filters reports by role', () => {
    expect(reportsForRole('administrator')).toHaveLength(6);
    expect(reportsForRole('trainer')).toHaveLength(6);
    expect(reportsForRole('client').map((report) => report.code)).toEqual(['REP-04']);
    expect(reportsForRole(undefined)).toEqual([]);
  });

  it('builds the detail route and finds reports by id', () => {
    const report = findReport('rep-03');
    expect(report?.code).toBe('REP-03');
    expect(report && reportPath(report)).toBe('/reports/rep-03');
    expect(findReport('rep-99')).toBeUndefined();
  });
});
