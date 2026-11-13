/**
 * Definiciones de columna y dirección de orden para `DataTable`.
 *
 * @remarks
 * Tipos genéricos para que cualquier feature (ejercicios, informes) pueda
 * declarar sus columnas sin que `DataTable` conozca la forma de los datos.
 * Se usa en `shared/components/DataTable` porque varias features lo reutilizan.
 */

/** Dirección de orden de una columna. */
export type SortDirection = 'asc' | 'desc' | undefined;

/**
 * Definición de una columna de la tabla.
 *
 * @template T - Tipo de cada fila (por ejemplo, un ejercicio o un informe).
 * @param accessor - Clave de la fila cuyo valor se muestra y ordena.
 * @param header - Texto del encabezado (en español, desde `messages.ts`).
 * @param sortable - Si el usuario puede ordenar por esta columna.
 * @param format - Opcional: convierte el valor crudo a texto para mostrar.
 */
export interface ColumnDef<T> {
  /** Clave de la fila cuyo valor se muestra y ordena. */
  accessor: keyof T;
  /** Texto del encabezado de la columna. */
  header: string;
  /** Si la columna permite ordenar. Por defecto `true`. */
  sortable?: boolean;
  /** Convierte el valor crudo en texto para mostrar (opcional). */
  format?: (value: T[keyof T]) => string;
  /** Renderiza contenido personalizado para una fila (opcional). */
  render?: (row: T) => ReactNode;
}
import type { ReactNode } from 'react';
