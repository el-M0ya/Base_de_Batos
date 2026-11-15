import { DataTable } from '../../shared/components/DataTable/DataTable';
import type { ColumnDef } from '../../shared/components/DataTable/columns';
import { messages } from '../../shared/i18n/messages';
import type { MuscleGroup } from '../../shared/types/muscleGroup';

const t = messages.muscleGroups;

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
  const columns: ColumnDef<MuscleGroup>[] = [
    { accessor: 'name', header: t.table.name },
    { accessor: 'description', header: t.table.description },
    {
      accessor: 'createdAt',
      header: t.table.created,
      format: (value) =>
        value === undefined
          ? messages.common.emptyValue
          : new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(new Date(String(value))),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={[...data]}
      loading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
      ariaLabel={t.tableLabel}
    />
  );
}
