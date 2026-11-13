import { useState, type FormEvent } from 'react';
import { useExerciseCatalogs } from './useExercises';
import type { Exercise, ExerciseClassificationInput } from './types';
import styles from './ExerciseForm.module.css';

/** Error shape accepted from the exercise update mutation. */
export type ExerciseBackendError = (Error & { status?: number }) | null | undefined;

/** Props for the exercise classification form. */
export interface ExerciseFormProps {
  /** Exercise whose classification is being edited. */
  exercise: Exercise;
  /** Closes the form without saving. */
  onCancel: () => void;
  /** Persists the selected classification. */
  onSubmit: (input: ExerciseClassificationInput) => Promise<void>;
  /** Disables the form while the update is pending. */
  isSubmitting: boolean;
  /** Error returned by the update operation. */
  backendError?: ExerciseBackendError;
}

interface ExerciseFormErrors {
  muscleGroupId?: string;
  exerciseType?: string;
  intensity?: string;
}

function getBackendErrorMessage(error: ExerciseBackendError): string | undefined {
  if (error === null || error === undefined) return undefined;
  if (error.status === 0) return 'No se pudo conectar con el servidor.';
  if (error.status === 403) return 'No tienes permiso para reclasificar este ejercicio.';
  if (error.status === 409) return error.message || 'La clasificación ya existe.';
  if (error.status === 422) return error.message || 'La clasificación no es válida.';
  return error.message || 'No se pudo actualizar el ejercicio.';
}

/**
 * Form for changing an exercise's muscle group, type and intensity.
 *
 * @remarks
 * The exercise identity fields are read-only. Catalog options are loaded
 * through the shared TanStack Query hook and submitted values are validated
 * before the parent mutation is called.
 */
export function ExerciseForm({
  exercise,
  onCancel,
  onSubmit,
  isSubmitting,
  backendError,
}: ExerciseFormProps) {
  const catalogsQuery = useExerciseCatalogs();
  const [muscleGroupId, setMuscleGroupId] = useState(exercise.muscleGroupId);
  const [exerciseType, setExerciseType] = useState(exercise.exerciseType);
  const [intensity, setIntensity] = useState(exercise.intensity);
  const [errors, setErrors] = useState<ExerciseFormErrors>({});

  const catalogError = catalogsQuery.error?.message ?? 'No se pudieron cargar los catálogos.';
  const backendErrorMessage = getBackendErrorMessage(backendError);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: ExerciseFormErrors = {};
    if (muscleGroupId.trim() === '') nextErrors.muscleGroupId = 'El grupo muscular es obligatorio.';
    if (exerciseType.trim() === '') nextErrors.exerciseType = 'El tipo de ejercicio es obligatorio.';
    if (intensity.trim() === '') nextErrors.intensity = 'La intensidad es obligatoria.';

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    await onSubmit({ muscleGroupId, exerciseType, intensity });
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      {backendErrorMessage !== undefined && (
        <p className={styles.error} role="alert">
          {backendErrorMessage}
        </p>
      )}

      <label className={styles.field}>
        <span>Nombre</span>
        <input className={styles.input} value={exercise.name} readOnly />
      </label>

      <label className={styles.field}>
        <span>Descripción</span>
        <textarea
          className={styles.input}
          value={exercise.description ?? ''}
          readOnly
          rows={3}
        />
      </label>

      {catalogsQuery.isLoading && (
        <p className={styles.status} role="status">
          Cargando catálogos…
        </p>
      )}
      {catalogsQuery.error !== null && catalogsQuery.error !== undefined && (
        <p className={styles.error} role="alert">
          {catalogError}
        </p>
      )}

      <label className={styles.field}>
        <span>Grupo muscular</span>
        <select
          className={styles.input}
          value={muscleGroupId}
          onChange={(event) => setMuscleGroupId(event.target.value)}
          disabled={isSubmitting}
          aria-invalid={errors.muscleGroupId !== undefined}
        >
          <option value="">Selecciona un grupo muscular</option>
          {(catalogsQuery.data?.muscleGroups ?? []).map((group) => (
            <option key={group.id} value={group.id}>
              {group.name}
            </option>
          ))}
        </select>
        {errors.muscleGroupId !== undefined && (
          <span className={styles.error} role="alert">
            {errors.muscleGroupId}
          </span>
        )}
      </label>

      <label className={styles.field}>
        <span>Tipo de ejercicio</span>
        <select
          className={styles.input}
          value={exerciseType}
          onChange={(event) => setExerciseType(event.target.value)}
          disabled={isSubmitting}
          aria-invalid={errors.exerciseType !== undefined}
        >
          <option value="">Selecciona un tipo</option>
          {(catalogsQuery.data?.exerciseTypes ?? []).map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        {errors.exerciseType !== undefined && (
          <span className={styles.error} role="alert">
            {errors.exerciseType}
          </span>
        )}
      </label>

      <label className={styles.field}>
        <span>Intensidad</span>
        <select
          className={styles.input}
          value={intensity}
          onChange={(event) => setIntensity(event.target.value)}
          disabled={isSubmitting}
          aria-invalid={errors.intensity !== undefined}
        >
          <option value="">Selecciona una intensidad</option>
          {(catalogsQuery.data?.intensityLevels ?? []).map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
        {errors.intensity !== undefined && (
          <span className={styles.error} role="alert">
            {errors.intensity}
          </span>
        )}
      </label>

      <div className={styles.actions}>
        <button type="button" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </button>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Guardando…' : 'Guardar cambios'}
        </button>
      </div>
    </form>
  );
}
