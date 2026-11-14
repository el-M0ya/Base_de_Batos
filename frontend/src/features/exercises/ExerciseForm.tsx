import { useState, type FormEvent } from 'react';
import { useExerciseCatalogs } from './useExercises';
import type { Exercise, ExerciseClassificationInput } from './types';
import { messages } from '../../shared/i18n/messages';
import styles from './ExerciseForm.module.css';

const t = messages.exercises;
const common = messages.common;

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
  if (error.status === 0) return common.networkError;
  if (error.status === 403) return t.errors.forbidden;
  if (error.status === 409) return error.message || t.errors.conflict;
  if (error.status === 422) return error.message || t.errors.invalid;
  return error.message || t.errors.updateFailed;
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

  const catalogError = catalogsQuery.error?.message ?? t.form.catalogsError;
  const backendErrorMessage = getBackendErrorMessage(backendError);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: ExerciseFormErrors = {};
    if (muscleGroupId.trim() === '') nextErrors.muscleGroupId = t.form.muscleGroupRequired;
    if (exerciseType.trim() === '') nextErrors.exerciseType = t.form.typeRequired;
    if (intensity.trim() === '') nextErrors.intensity = t.form.intensityRequired;

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
        <span>{t.form.nameLabel}</span>
        <input className={styles.input} value={exercise.name} readOnly />
      </label>

      <label className={styles.field}>
        <span>{t.form.descriptionLabel}</span>
        <textarea className={styles.input} value={exercise.description ?? ''} readOnly rows={3} />
      </label>

      {catalogsQuery.isLoading && (
        <p className={styles.status} role="status">
          {t.form.catalogsLoading}
        </p>
      )}
      {catalogsQuery.error !== null && catalogsQuery.error !== undefined && (
        <p className={styles.error} role="alert">
          {catalogError}
        </p>
      )}

      <label className={styles.field}>
        <span>{t.form.muscleGroupLabel}</span>
        <select
          className={styles.input}
          value={muscleGroupId}
          onChange={(event) => setMuscleGroupId(event.target.value)}
          disabled={isSubmitting}
          aria-invalid={errors.muscleGroupId !== undefined}
        >
          <option value="">{t.form.muscleGroupPlaceholder}</option>
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
        <span>{t.form.typeLabel}</span>
        <select
          className={styles.input}
          value={exerciseType}
          onChange={(event) => setExerciseType(event.target.value)}
          disabled={isSubmitting}
          aria-invalid={errors.exerciseType !== undefined}
        >
          <option value="">{t.form.typePlaceholder}</option>
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
        <span>{t.form.intensityLabel}</span>
        <select
          className={styles.input}
          value={intensity}
          onChange={(event) => setIntensity(event.target.value)}
          disabled={isSubmitting}
          aria-invalid={errors.intensity !== undefined}
        >
          <option value="">{t.form.intensityPlaceholder}</option>
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
          {common.cancel}
        </button>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? t.form.saving : common.saveChanges}
        </button>
      </div>
    </form>
  );
}
