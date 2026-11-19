import { DataTable } from '../../shared/components/DataTable/DataTable';
import type { SortDirection } from '../../shared/components/DataTable/columns';
import { useAuth } from '../../shared/auth/useAuth';
import { messages } from '../../shared/i18n/messages';
import { exerciseColumns } from './exerciseColumns';
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
  /** Notifies the active sort, so the page can export rows in the same order. */
  onSortChange?: (accessor: keyof Exercise | null, direction: SortDirection) => void;
}

/**
 * Displays exercises and exposes reclassification only to their creating trainer.
 */
export function ExerciseTable({
  exercises,
  loading = false,
  onReclassify,
  onSortChange,
}: ExerciseTableProps) {
  const { user } = useAuth();

  const canEdit = (exercise: Exercise) =>
    user?.role === 'trainer' && String(exercise.trainerId) === String(user.id);

  return (
    <DataTable
      columns={exerciseColumns}
      data={exercises}
      loading={loading}
      onSortChange={onSortChange}
      onEdit={onReclassify}
      canEdit={canEdit}
      ariaLabel={t.tableLabel}
    />
  );
}
