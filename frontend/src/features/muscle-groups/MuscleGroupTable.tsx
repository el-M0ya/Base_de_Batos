import { DataTable, type DataTableColumn } from '../../shared/components/DataTable';
import type { MuscleGroup } from './types';

/** Props for the muscle-group table. */
export interface MuscleGroupTableProps {
  /** Records to display. */
  data: readonly MuscleGroup[];
  /** Whether the catalog request is in progress. */
  isLoading?: boolean;
  /** Opens the edit form for a record. */
  onEdit: (group: MuscleGroup) => void;
  /** Starts the delete flow for a record. */
  onDelete: (group: MuscleGroup) => void;
}

/**
 * Catalog table for muscle groups.
 *
 * @remarks
 * This feature-specific wrapper keeps the shared DataTable contract out of
 * the page and makes a future E3-04 table replacement local to this module.
 */
export function MuscleGroupTable({
  data,
  isLoading = false,
  onEdit,
  onDelete,
}: MuscleGroupTableProps) {
  const columns: readonly DataTableColumn<MuscleGroup>[] = [
    { key: 'name', header: 'Nombre' },
    { key: 'description', header: 'Descripción' },
    {
      key: 'createdAt',
      header: 'Creado',
      render: (group) =>
        group.createdAt === undefined
          ? '—'
          : new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(
              new Date(group.createdAt),
            ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      getRowKey={(group) => group.id}
      onEdit={onEdit}
      onDelete={onDelete}
      emptyMessage="No hay grupos musculares registrados."
      ariaLabel="Catálogo de grupos musculares"
    />
  );
}
