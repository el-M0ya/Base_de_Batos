/**
 * Pure sorting used by `useSort` (the table on screen) and by anything that
 * needs the rows in the same order the user sees, such as the PDF export.
 *
 * @remarks
 * Stable (equal values keep their original order), empty values always go
 * last, and text is compared with the browser locale ignoring accents
 * (sensitivity: 'base'), so "Ángulo" sorts next to "A".
 */

/** Returns true for values shown as empty. */
function isEmptyValue(value: unknown): boolean {
  return value === undefined || value === null || value === '';
}

/**
 * Returns a new array with the rows sorted by one column.
 *
 * @template T - Type of each row.
 * @param rows - Rows to sort (not modified).
 * @param accessor - Row key to sort by.
 * @param direction - Ascending or descending.
 */
export function sortRows<T extends object>(
  rows: T[],
  accessor: keyof T,
  direction: 'asc' | 'desc',
): T[] {
  const collator = new Intl.Collator(undefined, { sensitivity: 'base', numeric: true });

  function compare(a: T, b: T): number {
    const av = a[accessor];
    const bv = b[accessor];
    const aEmpty = isEmptyValue(av);
    const bEmpty = isEmptyValue(bv);

    // Empty values always last, whatever the direction.
    if (aEmpty || bEmpty) {
      return Number(aEmpty) - Number(bEmpty);
    }

    const cmp =
      typeof av === 'number' && typeof bv === 'number'
        ? av - bv
        : collator.compare(String(av), String(bv));
    return direction === 'asc' ? cmp : -cmp;
  }

  // Stable sort: ties fall back to the original index.
  return rows
    .map((row, index) => ({ row, index }))
    .sort((x, y) => compare(x.row, y.row) || x.index - y.index)
    .map(({ row }) => row);
}
