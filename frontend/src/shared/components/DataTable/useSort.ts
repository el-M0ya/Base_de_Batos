import { useCallback, useMemo, useState } from 'react';
import { sortRows } from './sortRows';

/**
 * Hook de ordenamiento reutilizable para `DataTable`.
 *
 * @remarks
 * Guarda la columna y la dirección activas; el orden en sí lo hace la función
 * pura `sortRows`, que también usan otros consumidores (por ejemplo, la
 * exportación a PDF) para obtener exactamente el mismo orden que la pantalla.
 *
 * @template T - Tipo de cada fila.
 * @param rows - Filas a ordenar.
 * @param initialAccessor - Clave de la fila por la que ordenar al empezar.
 */
export function useSort<T extends object>(rows: T[], initialAccessor: keyof T) {
  const [sortAccessor, setSortAccessor] = useState<keyof T>(initialAccessor);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const sorted = useMemo(
    () => sortRows(rows, sortAccessor, sortDirection),
    [rows, sortAccessor, sortDirection],
  );

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
