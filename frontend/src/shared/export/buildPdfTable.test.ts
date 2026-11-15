import { describe, expect, it } from 'vitest';
import type { ColumnDef } from '../components/DataTable/columns';
import { buildPdfTable } from './buildPdfTable';

interface Row {
  name: string;
  load: number | null;
  date: string;
  status: string;
}

const columns: ColumnDef<Row>[] = [
  { accessor: 'name', header: 'Nombre' },
  { accessor: 'load', header: 'Carga' },
  { accessor: 'date', header: 'Fecha', format: (value) => `día ${String(value)}` },
  { accessor: 'status', header: 'Estado', exportable: false },
];

const rows: Row[] = [
  { name: 'Sentadilla', load: 80, date: '01/11', status: 'ok' },
  { name: 'Press banca', load: null, date: '02/11', status: 'ok' },
];

describe('buildPdfTable', () => {
  it('uses the column headers, skipping non-exportable columns', () => {
    expect(buildPdfTable(columns, rows).head).toEqual(['Nombre', 'Carga', 'Fecha']);
  });

  it('converts cells to text, applying format and the empty marker', () => {
    expect(buildPdfTable(columns, rows).body).toEqual([
      ['Sentadilla', '80', 'día 01/11'],
      ['Press banca', '—', 'día 02/11'],
    ]);
  });

  it('keeps the row order it receives (the caller already sorted them)', () => {
    const body = buildPdfTable(columns, [...rows].reverse()).body;
    expect(body.map((cells) => cells[0])).toEqual(['Press banca', 'Sentadilla']);
  });

  it('returns an empty body when there are no rows', () => {
    expect(buildPdfTable(columns, []).body).toEqual([]);
  });
});
