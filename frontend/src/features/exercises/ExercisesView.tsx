import { useState } from 'react';
import { useAuth } from '../../shared/auth/useAuth';
import { ExerciseForm } from './ExerciseForm';
import { ExerciseTable } from './ExerciseTable';
import { useExercises, useUpdateExerciseClassification } from './useExercises';
import type { Exercise, ExerciseClassificationInput } from './types';
import styles from './ExercisesView.module.css';

function isExerciseOwner(exercise: Exercise, user: ReturnType<typeof useAuth>['user']) {
  return user?.role === 'trainer' && String(exercise.trainerId) === String(user.id);
}

/** Coordinates the exercise list, reclassification modal and update mutation. */
export function ExercisesView() {
  const { user } = useAuth();
  const exercisesQuery = useExercises();
  const updateMutation = useUpdateExerciseClassification();
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);

  const exercises = exercisesQuery.data ?? [];

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

  return (
    <section className={styles.view} aria-labelledby="exercises-title">
      <div className={styles.header}>
        <div>
          <h1 id="exercises-title">Ejercicios</h1>
          <p>Consulta y reclasifica los ejercicios que has creado.</p>
        </div>
      </div>

      {exercisesQuery.error !== null && exercisesQuery.error !== undefined && (
        <p className={styles.error} role="alert">
          {exercisesQuery.error.message || 'No se pudieron cargar los ejercicios.'}
        </p>
      )}

      <ExerciseTable
        exercises={exercises}
        loading={exercisesQuery.isLoading}
        onReclassify={handleReclassify}
      />

      {selectedExercise !== null && (
        <div className={styles.overlay} role="presentation">
          <div
            className={styles.modal}
            role="dialog"
            aria-modal="true"
            aria-labelledby="exercise-form-title"
          >
            <div className={styles.modalHeader}>
              <h2 id="exercise-form-title">Reclasificar ejercicio</h2>
              <button
                type="button"
                className={styles.close}
                onClick={() => setSelectedExercise(null)}
                disabled={updateMutation.isPending}
                aria-label="Cerrar formulario"
              >
                ×
              </button>
            </div>
            <ExerciseForm
              exercise={selectedExercise}
              onCancel={() => setSelectedExercise(null)}
              onSubmit={handleSubmit}
              isSubmitting={updateMutation.isPending}
              backendError={updateMutation.error}
            />
          </div>
        </div>
      )}
    </section>
  );
}
