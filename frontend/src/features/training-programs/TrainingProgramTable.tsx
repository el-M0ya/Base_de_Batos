import { DataTable } from '../../shared/components/DataTable/DataTable';
import type { ColumnDef } from '../../shared/components/DataTable/columns';
import type { TrainingProgram } from './types';

/** Props for the training-program table. */
export interface TrainingProgramTableProps {
  /** Programs to display. */
  data: readonly TrainingProgram[];
  /** Whether the catalog request is in progress. */
  isLoading?: boolean;
  /** Opens the edit form. */
  onEdit: (program: TrainingProgram) => void;
  /** Starts the delete flow. */
  onDelete: (program: TrainingProgram) => void;
}

/**
 * DataTable wrapper for training programs.
 *
 * @remarks
 * Keeping this adapter feature-local allows the official E3-04 table to
 * replace the temporary shared component without changing the page.
 */
export function TrainingProgramTable({
  data,
  isLoading = false,
  onEdit,
  onDelete,
}: TrainingProgramTableProps) {
  const columns: ColumnDef<TrainingProgram>[] = [
    { accessor: 'name', header: 'Nombre' },
    { accessor: 'objective', header: 'Objetivo' },
    {
      accessor: 'muscleGroupIds',
      header: 'Grupos musculares',
      format: (value) => `${Array.isArray(value) ? value.length : 0} configurado(s)`,
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={[...data]}
      loading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
      ariaLabel="Catálogo de programas de entrenamiento"
    />
  );
}
