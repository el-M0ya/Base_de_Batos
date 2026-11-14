/**
 * Tabla de datos genérica, ordenable y accesible.
 *
 * @remarks
 * Componente presentacional reutilizado por el módulo de ejercicios (E3-08)
 * y los seis informes (E3-09). La lógica de orden vive en `useSort`; esta
 * tabla solo renderiza columnas, filas y estados (carga / vacía).
 * Expone el estado activo de orden a través de `onSortChange` para que
 * consumidores como la exportación a PDF respeten el orden activo.
 *
 * @template T - Tipo de cada fila.
 * @param columns - Definiciones de columna.
 * @param data - Filas a mostrar.
 * @param loading - Cuando true, muestra el estado de carga en lugar de la tabla.
 * @param onSortChange - Se invoca cuando el usuario cambia el orden activo.
 */
import { Pencil, Trash2 } from 'lucide-react';
import { useSort } from './useSort';
import type { ColumnDef, SortDirection } from './columns';
import { Button } from '../Button';
import { messages } from '../../i18n/messages';
import styles from './DataTable.module.css';

const t = messages.dataTable;

/**
 * Props de `DataTable`.
 *
 * @template T - Tipo de cada fila.
 */
export interface DataTableProps<T> {
  /** Definiciones de columna. */
  columns: ColumnDef<T>[];
  /** Filas a mostrar. */
  data: T[];
  /** Cuando true, muestra el estado de carga en lugar de la tabla. */
  loading?: boolean;
  /**
   * Notifica el cambio de orden activo.
   * Recibe la columna y la dirección resultante.
   */
  onSortChange?: (accessor: keyof T | null, direction: SortDirection) => void;
  /** Invoked when the user requests editing a row. */
  onEdit?: (row: T) => void;
  /** Controls whether the edit action is shown for a row. */
  canEdit?: (row: T) => boolean;
  /** Invoked when the user requests deleting a row. */
  onDelete?: (row: T) => void;
  /** Accessible label for the table. */
  ariaLabel?: string;
}

/**
 * Tabla de datos ordenable.
 *
 * @example
 * ```tsx
 * <DataTable
 *   columns={columns}
 *   data={rows}
 *   onSortChange={(accessor, direction) => setSort({ accessor, direction })}
 * />
 * ```
 */
export function DataTable<T extends object>({
  columns,
  data,
  loading = false,
  onSortChange,
  onEdit,
  canEdit,
  onDelete,
  ariaLabel = t.defaultLabel,
}: DataTableProps<T>) {
  const firstSortable =
    columns.find((c) => c.sortable !== false)?.accessor ?? (columns[0]?.accessor as keyof T);

  const { sorted, sortAccessor, sortDirection, setSort } = useSort(data, firstSortable);

  const isEmpty = !loading && data.length === 0;

  function handleHeaderClick(accessor: keyof T) {
    setSort(accessor);
    // Misma lógica que `setSort` internamente: asc → desc → asc.
    const direction: SortDirection =
      sortAccessor === accessor && sortDirection === 'asc' ? 'desc' : 'asc';
    onSortChange?.(accessor, direction);
  }

  const hasActions = onEdit !== undefined || onDelete !== undefined;
  if (loading) {
    return (
      <div className={styles.loading} role="status" aria-label={t.loadingLabel}>
        {messages.states.loading}
      </div>
    );
  }

  if (isEmpty) {
    return <div className={styles.empty}>{t.empty}</div>;
  }

  return (
    <table className={styles.table} aria-label={ariaLabel}>
      <caption className={styles.caption}>{t.caption(sorted.length)}</caption>
      <thead className={styles.thead}>
        <tr>
          {columns.map((column) => {
            const isActive = sortAccessor === column.accessor;
            return (
              <th
                key={String(column.accessor)}
                className={[
                  styles.th,
                  column.sortable !== false ? styles.sortable : '',
                  isActive ? styles.active : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
                scope="col"
              >
                {column.sortable !== false ? (
                  <button
                    onClick={() => handleHeaderClick(column.accessor)}
                    aria-sort={
                      isActive ? (sortDirection === 'asc' ? 'ascending' : 'descending') : undefined
                    }
                    aria-label={
                      isActive
                        ? t.sortBy(column.header, sortDirection === 'asc' ? 'desc' : 'asc')
                        : t.sortBy(column.header, 'asc')
                    }
                  >
                    {column.header}
                    <span className={styles.sortIndicator}>
                      {isActive ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
                    </span>
                  </button>
                ) : (
                  column.header
                )}
              </th>
            );
          })}
          {hasActions && (
            <th className={styles.th} scope="col">
              {t.actions}
            </th>
          )}
        </tr>
      </thead>
      <tbody className={styles.tbody}>
        {sorted.map((row, rowIndex) => (
          <tr key={String(rowIndex)}>
            {columns.map((column) => {
              const value = row[column.accessor];
              const text =
                column.render !== undefined
                  ? column.render(row)
                  : column.format !== undefined
                    ? column.format(value)
                    : String(value ?? '');
              return <td key={String(column.accessor)}>{text}</td>;
            })}
            {hasActions && (
              <td>
                {onEdit !== undefined && canEdit?.(row) !== false && (
                  <Button
                    variant="ghost"
                    onClick={() => onEdit(row)}
                    aria-label={t.editRow(rowIndex + 1)}
                    title={t.edit}
                    icon={<Pencil size={16} aria-hidden="true" />}
                  >
                    {t.edit}
                  </Button>
                )}
                {onDelete !== undefined && (
                  <Button
                    variant="ghost"
                    onClick={() => onDelete(row)}
                    aria-label={t.deleteRow(rowIndex + 1)}
                    title={t.delete}
                    icon={<Trash2 size={16} aria-hidden="true" />}
                  >
                    {t.delete}
                  </Button>
                )}
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
