import { useState } from 'react';
import { useAuth } from '../../shared/auth/useAuth';
import { Alert } from '../../shared/components/Alert';
import { ExportPdfButton } from '../../shared/components/ExportPdfButton';
import type { SortDirection } from '../../shared/components/DataTable/columns';
import { sortRows } from '../../shared/components/DataTable/sortRows';
import { buildPdfTable } from '../../shared/export/buildPdfTable';
import type { PdfExportOptions } from '../../shared/export/exportToPdf';
import { Modal } from '../../shared/components/Modal';
import { ExerciseForm } from './ExerciseForm';
import { ExerciseTable } from './ExerciseTable';
import { exerciseColumns } from './exerciseColumns';
import { useExercises, useUpdateExerciseClassification } from './useExercises';
import type { Exercise, ExerciseClassificationInput } from './types';
import { messages } from '../../shared/i18n/messages';
import styles from './ExercisesView.module.css';

const t = messages.exercises;

/** Active sort of the table, mirrored here so the PDF keeps the same order. */
interface ExerciseSort {
  accessor: keyof Exercise;
  direction: 'asc' | 'desc';
}

// Same starting sort as DataTable: first sortable column, ascending.
const INITIAL_SORT: ExerciseSort = {
  accessor: exerciseColumns.find((column) => column.sortable !== false)?.accessor ?? 'name',
  direction: 'asc',
};

function isExerciseOwner(exercise: Exercise, user: ReturnType<typeof useAuth>['user']) {
  return user?.role === 'trainer' && String(exercise.trainerId) === String(user.id);
}

/** Coordinates the exercise list, reclassification modal and update mutation. */
export function ExercisesView() {
  const { user } = useAuth();
  const exercisesQuery = useExercises();
  const updateMutation = useUpdateExerciseClassification();
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);
  const [sort, setSort] = useState<ExerciseSort>(INITIAL_SORT);

  const exercises = exercisesQuery.data ?? [];

  function handleSortChange(accessor: keyof Exercise | null, direction: SortDirection) {
    if (accessor !== null) {
      setSort({ accessor, direction: direction ?? 'asc' });
    }
  }

  // Called at click time: exports the rows in the order currently on screen.
  function getExport(): PdfExportOptions {
    const rows = sortRows(exercises, sort.accessor, sort.direction);
    return {
      title: t.title,
      fileName: t.pdfFileName,
      table: buildPdfTable(exerciseColumns, rows),
    };
  }

  function handleReclassify(exercise: Exercise) {
    if (isExerciseOwner(exercise, user)) {
      setSelectedExercise(exercise);
    }
  }

  async function handleSubmit(input: ExerciseClassificationInput) {
    if (selectedExercise === null) return;

    await updateMutation.mutateAsync({
      id: selectedExercise.id,
      input,
    });
    setSelectedExercise(null);
  }

  // Closing is ignored while saving, whatever the trigger (✕, Escape or a
  // click outside), so the form is never dismissed halfway through a save.
  function closeForm() {
    if (updateMutation.isPending) return;
    setSelectedExercise(null);
  }

  return (
    <section className={styles.view} aria-labelledby="exercises-title">
      <div className={styles.header}>
        <div>
          <h1 id="exercises-title">{t.title}</h1>
          <p>{t.subtitle}</p>
        </div>
        <ExportPdfButton
          getExport={getExport}
          disabled={exercisesQuery.isLoading || exercises.length === 0}
        />
      </div>

      {exercisesQuery.error !== null && exercisesQuery.error !== undefined && (
        <Alert>{exercisesQuery.error.message || t.loadError}</Alert>
      )}

      <ExerciseTable
        exercises={exercises}
        loading={exercisesQuery.isLoading}
        onReclassify={handleReclassify}
        onSortChange={handleSortChange}
      />

      <Modal isOpen={selectedExercise !== null} onClose={closeForm} title={t.form.title}>
        {selectedExercise !== null && (
          <ExerciseForm
            exercise={selectedExercise}
            onCancel={closeForm}
            onSubmit={handleSubmit}
            isSubmitting={updateMutation.isPending}
            backendError={updateMutation.error}
          />
        )}
      </Modal>
    </section>
  );
}
