import { describe, expect, it } from 'vitest';
import { sortRows } from './sortRows';

interface Row {
  id: number;
  name: string | null;
  load: number;
}

const rows: Row[] = [
  { id: 1, name: 'Remo', load: 40 },
  { id: 2, name: null, load: 10 },
  { id: 3, name: 'Ángulo', load: 40 },
  { id: 4, name: 'banco', load: 25 },
];

const ids = (sorted: Row[]) => sorted.map((row) => row.id);

describe('sortRows', () => {
  it('sorts text ignoring accents and case, with empty values last', () => {
    expect(ids(sortRows(rows, 'name', 'asc'))).toEqual([3, 4, 1, 2]);
    expect(ids(sortRows(rows, 'name', 'desc'))).toEqual([1, 4, 3, 2]);
  });

  it('sorts numbers and keeps the original order of ties', () => {
    expect(ids(sortRows(rows, 'load', 'asc'))).toEqual([2, 4, 1, 3]);
  });

  it('does not modify the received array', () => {
    sortRows(rows, 'load', 'desc');
    expect(ids(rows)).toEqual([1, 2, 3, 4]);
  });
});
