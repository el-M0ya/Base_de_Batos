import { DataTable } from '../../shared/components/DataTable/DataTable';
import type { ColumnDef } from '../../shared/components/DataTable/columns';
import { useAuth } from '../../shared/auth/useAuth';
import type { Exercise } from './types';

/** Props for the exercise catalog table. */
export interface ExerciseTableProps {
  /** Exercises to display. */
  exercises: Exercise[];
  /** Shows the shared table loading state. */
  loading?: boolean;
  /** Handles a permitted exercise reclassification request. */
  onReclassify: (exercise: Exercise) => void;
}

const columns: ColumnDef<Exercise>[] = [
  { accessor: 'name', header: 'Nombre' },
  { accessor: 'muscleGroupName', header: 'Grupo muscular' },
  { accessor: 'exerciseType', header: 'Tipo' },
  { accessor: 'intensity', header: 'Intensidad' },
  { accessor: 'trainerId', header: 'Creador' },
  {
    accessor: 'registrationDate',
    header: 'Fecha de registro',
    format: (value) => value ?? '-',
  },
];

/**
 * Displays exercises and exposes reclassification only to their creating trainer.
 */
export function ExerciseTable({ exercises, loading = false, onReclassify }: ExerciseTableProps) {
  const { user } = useAuth();

  const canEdit = (exercise: Exercise) =>
    user?.role === 'trainer' && String(exercise.trainerId) === String(user.id);

  return (
    <DataTable
      columns={columns}
      data={exercises}
      loading={loading}
      onEdit={onReclassify}
      canEdit={canEdit}
      ariaLabel="Tabla de ejercicios"
    />
  );
}
