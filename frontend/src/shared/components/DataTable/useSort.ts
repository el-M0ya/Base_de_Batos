import { useCallback, useMemo, useState } from 'react';

/**
 * Hook de ordenamiento reutilizable para `DataTable`.
 *
 * @remarks
 * Centraliza la lógica de orden para que no se reimplente en cada feature.
 * Es estable (mantiene el orden relativo de valores iguales), coloca los
 * valores vacíos/nulo siempre al final y compara texto con el locale del
 * navegador ignorando los acentos (sensitivity: 'base'), de modo que
 * "Ángulo" se ordena junto a "A".
 *
 * @template T - Tipo de cada fila.
 * @param rows - Filas a ordenar.
 * @param initialAccessor - Clave de la fila por la que ordenar al empezar.
 */
export function useSort<T extends object>(rows: T[], initialAccessor: keyof T) {
  const [sortAccessor, setSortAccessor] = useState<keyof T>(initialAccessor);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  /** Comparador que respeta el locale, ignora acentos y deja vacíos al final. */
  const compare = useMemo(() => {
    const collator = new Intl.Collator(undefined, {
      sensitivity: 'base',
      numeric: true,
    });

    return (a: T, b: T): number => {
      const av = a[sortAccessor];
      const bv = b[sortAccessor];

      const aEmpty = av === undefined || av === null || av === '';
      const bEmpty = bv === undefined || bv === null || bv === '';

      // Vacíos siempre al final, sin importar la dirección.
      if (aEmpty && bEmpty) {
        return 0;
      }
      if (aEmpty) {
        return 1;
      }
      if (bEmpty) {
        return -1;
      }

      let cmp: number;
      if (typeof av === 'string' || typeof bv === 'string') {
        cmp = collator.compare(String(av), String(bv));
      } else if (typeof av === 'number' && typeof bv === 'number') {
        cmp = av - bv;
      } else {
        cmp = collator.compare(String(av ?? ''), String(bv ?? ''));
      }

      // Orden estable: si son iguales, conserva el orden original.
      if (cmp === 0) {
        return 0;
      }

      return sortDirection === 'asc' ? cmp : -cmp;
    };
  }, [sortAccessor, sortDirection]);

  const sorted = useMemo(() => {
    // Orden estable: ordenamos por (valor, índice original).
    const indexed = rows.map((row, index) => ({ row, index }));
    indexed.sort(({ row: a, index: ia }, { row: b, index: ib }) => {
      const cmp = compare(a, b);
      if (cmp !== 0) {
        return cmp;
      }
      return ia - ib;
    });
    return indexed.map(({ row }) => row);
  }, [rows, compare]);

  /**
   * Cambia la columna por la que se ordena.
   * Si es la misma columna, alterna la dirección; si es distinta, empieza en asc.
   */
  const setSort = useCallback(
    (accessor: keyof T) => {
      setSortAccessor(accessor);
      setSortDirection((prev) => (prev === 'asc' && accessor === sortAccessor ? 'desc' : 'asc'));
    },
    [sortAccessor],
  );

  return {
    sorted,
    sortAccessor,
    sortDirection,
    setSort,
  };
}
