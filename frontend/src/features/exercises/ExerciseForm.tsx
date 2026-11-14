import { useState, type FormEvent } from 'react';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { LoadingState } from '../../shared/components/LoadingState';
import { SelectField, type SelectOption } from '../../shared/components/SelectField';
import { TextField } from '../../shared/components/TextField';
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

  // SelectField expects { value, label } pairs; the catalogs come in other shapes.
  const muscleGroupOptions: SelectOption[] = (catalogsQuery.data?.muscleGroups ?? []).map(
    (group) => ({ value: group.id, label: group.name }),
  );
  const typeOptions: SelectOption[] = (catalogsQuery.data?.exerciseTypes ?? []).map((type) => ({
    value: type,
    label: type,
  }));
  const intensityOptions: SelectOption[] = (catalogsQuery.data?.intensityLevels ?? []).map(
    (level) => ({ value: level, label: level }),
  );

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      {backendErrorMessage !== undefined && <Alert>{backendErrorMessage}</Alert>}

      <TextField label={t.form.nameLabel} value={exercise.name} readOnly />

      {/* TODO: replace with the shared TextArea component once it exists. */}
      <label className={styles.field}>
        <span className={styles.label}>{t.form.descriptionLabel}</span>
        <textarea
          className={styles.textarea}
          value={exercise.description ?? ''}
          readOnly
          rows={3}
        />
      </label>

      {catalogsQuery.isLoading && <LoadingState message={t.form.catalogsLoading} />}
      {catalogsQuery.error !== null && catalogsQuery.error !== undefined && (
        <Alert>{catalogError}</Alert>
      )}

      <SelectField
        label={t.form.muscleGroupLabel}
        placeholder={t.form.muscleGroupPlaceholder}
        options={muscleGroupOptions}
        value={muscleGroupId}
        onChange={(event) => setMuscleGroupId(event.target.value)}
        error={errors.muscleGroupId}
        disabled={isSubmitting}
      />

      <SelectField
        label={t.form.typeLabel}
        placeholder={t.form.typePlaceholder}
        options={typeOptions}
        value={exerciseType}
        onChange={(event) => setExerciseType(event.target.value)}
        error={errors.exerciseType}
        disabled={isSubmitting}
      />

      <SelectField
        label={t.form.intensityLabel}
        placeholder={t.form.intensityPlaceholder}
        options={intensityOptions}
        value={intensity}
        onChange={(event) => setIntensity(event.target.value)}
        error={errors.intensity}
        disabled={isSubmitting}
      />

      <div className={styles.actions}>
        <Button variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          {common.cancel}
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {common.saveChanges}
        </Button>
      </div>
    </form>
  );
}
