import { DataTable, type DataTableColumn } from '../../shared/components/DataTable';
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
  const columns: readonly DataTableColumn<TrainingProgram>[] = [
    { key: 'name', header: 'Nombre' },
    { key: 'objective', header: 'Objetivo' },
    {
      key: 'muscleGroupIds',
      header: 'Grupos musculares',
      render: (program) =>
        program.muscleGroups?.map((group) => group.name).join(', ') ??
        `${program.muscleGroupIds.length} configurado(s)`,
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      getRowKey={(program) => program.id}
      onEdit={onEdit}
      onDelete={onDelete}
      emptyMessage="No hay programas de entrenamiento registrados."
      ariaLabel="Catálogo de programas de entrenamiento"
    />
  );
}
