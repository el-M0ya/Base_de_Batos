import type { ReactNode } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import { Button } from './Button';
import styles from './DataTable.module.css';

/**
 * Describes one column rendered by {@link DataTable}.
 *
 * @template T - Type of the records shown in the table.
 */
export interface DataTableColumn<T> {
  /**
   * Stable identifier for the column and the default property used to read
   * its value from a row.
   */
  key: keyof T;
  /** Accessible and visible heading for the column. */
  header: string;
  /**
   * Optional cell renderer for formatting values or rendering custom content.
   * When omitted, the value at `key` is converted to text.
   */
  render?: (row: T) => ReactNode;
  /** Optional class name applied to the heading and cells in this column. */
  className?: string;
}

/**
 * Props accepted by the temporary shared data table.
 *
 * @remarks
 * The API intentionally keeps data access and row actions independent from
 * feature-specific models. A future E3-04 implementation can preserve these
 * contracts, or adapt them in one place, without changing CRUD pages.
 *
 * @template T - Type of the records shown in the table.
 */
export interface DataTableProps<T> {
  /** Columns to render from left to right. */
  columns: readonly DataTableColumn<T>[];
  /** Records displayed in the table. */
  data: readonly T[];
  /** Shows a loading row and prevents the table from displaying stale state. */
  isLoading?: boolean;
  /** Optional function used to produce a stable React key for each row. */
  getRowKey?: (row: T, index: number) => string | number;
  /** Called when the user requests editing a row. */
  onEdit?: (row: T) => void;
  /** Called when the user requests deleting a row. */
  onDelete?: (row: T) => void;
  /** Text shown while data is being loaded. */
  loadingMessage?: string;
  /** Text shown when the request succeeds but returns no records. */
  emptyMessage?: string;
  /** Accessible label for the table. */
  ariaLabel?: string;
}

/**
 * Generic table for CRUD-oriented list screens.
 *
 * @remarks
 * This is a deliberately small temporary abstraction for Issue #109. It
 * delegates presentation of values to columns and behavior of mutations to
 * callbacks, so the component does not know anything about a specific domain
 * entity or API implementation.
 *
 * The edit and delete controls are rendered only when their corresponding
 * callbacks are provided. This allows read-only tables to reuse the same
 * component without showing inactive actions.
 *
 * @example
 * ```tsx
 * <DataTable
 *   columns={[
 *     { key: 'name', header: 'Nombre' },
 *     { key: 'status', header: 'Estado', render: (site) => site.statusLabel },
 *   ]}
 *   data={sites}
 *   getRowKey={(site) => site.id}
 *   onEdit={openEditForm}
 *   onDelete={requestDelete}
 * />
 * ```
 *
 * @template T - Type of the records shown in the table.
 */
export function DataTable<T>({
  columns,
  data,
  isLoading = false,
  getRowKey = (_row, index) => index,
  onEdit,
  onDelete,
  loadingMessage = 'Cargando datos…',
  emptyMessage = 'No hay registros para mostrar.',
  ariaLabel = 'Tabla de datos',
}: DataTableProps<T>) {
  const hasActions = onEdit !== undefined || onDelete !== undefined;
  const columnCount = columns.length + (hasActions ? 1 : 0);

  return (
    <div className={styles.container}>
      <div className={styles.scroller}>
        <table className={styles.table} aria-label={ariaLabel}>
          <thead className={styles.head}>
            <tr>
              {columns.map((column) => (
                <th key={String(column.key)} className={column.className} scope="col">
                  {column.header}
                </th>
              ))}
              {hasActions && (
                <th className={styles.actionsHeading} scope="col">
                  Acciones
                </th>
              )}
            </tr>
          </thead>

          <tbody>
            {isLoading ? (
              <tr>
                <td className={styles.message} colSpan={columnCount}>
                  <span className={styles.loadingIndicator} aria-hidden="true" />
                  <span role="status">{loadingMessage}</span>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td className={styles.message} colSpan={columnCount}>
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr key={getRowKey(row, index)} className={styles.row}>
                  {columns.map((column) => (
                    <td key={String(column.key)} className={column.className}>
                      {column.render !== undefined
                        ? column.render(row)
                        : String(row[column.key] ?? '')}
                    </td>
                  ))}
                  {hasActions && (
                    <td className={styles.actions}>
                      {onEdit !== undefined && (
                        <Button
                          variant="ghost"
                          className={styles.actionButton}
                          onClick={() => onEdit(row)}
                          aria-label={`Editar registro ${index + 1}`}
                          title="Editar"
                          icon={<Pencil size={16} aria-hidden="true" />}
                        >
                          Editar
                        </Button>
                      )}
                      {onDelete !== undefined && (
                        <Button
                          variant="ghost"
                          className={`${styles.actionButton} ${styles.deleteButton}`}
                          onClick={() => onDelete(row)}
                          aria-label={`Eliminar registro ${index + 1}`}
                          title="Eliminar"
                          icon={<Trash2 size={16} aria-hidden="true" />}
                        >
                          Eliminar
                        </Button>
                      )}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
