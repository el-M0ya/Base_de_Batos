import { DataTable } from '../../shared/components/DataTable/DataTable';
import type { ColumnDef } from '../../shared/components/DataTable/columns';
import { useAuth } from '../../shared/auth/useAuth';
import { messages } from '../../shared/i18n/messages';
import type { Exercise } from './types';

const t = messages.exercises;

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
  { accessor: 'name', header: t.table.name },
  { accessor: 'muscleGroupName', header: t.table.muscleGroup },
  { accessor: 'exerciseType', header: t.table.type },
  { accessor: 'intensity', header: t.table.intensity },
  { accessor: 'trainerId', header: t.table.creator },
  {
    accessor: 'registrationDate',
    header: t.table.registrationDate,
    format: (value) => value ?? messages.common.emptyValue,
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
      ariaLabel={t.tableLabel}
    />
  );
}
