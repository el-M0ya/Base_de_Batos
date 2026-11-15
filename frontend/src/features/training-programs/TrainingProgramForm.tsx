import { useState, type FormEvent } from 'react';
import { ApiError } from '../../shared/api/apiError';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { LoadingState } from '../../shared/components/LoadingState';
import { TextField } from '../../shared/components/TextField';
import { TrainingProgramMuscleGroups } from './TrainingProgramMuscleGroups';
import type { MuscleGroup } from '../../shared/types/muscleGroup';
import type { TrainingProgram, TrainingProgramInput } from './types';
import { messages } from '../../shared/i18n/messages';
import styles from './TrainingProgramForm.module.css';

const t = messages.trainingPrograms;
const common = messages.common;

/** Props for the create/edit training-program form. */
export interface TrainingProgramFormProps {
  /** Existing program when editing; omitted in create mode. */
  initialValue?: TrainingProgram | undefined;
  /** Muscle-group options loaded from the catalog API. */
  muscleGroups: readonly MuscleGroup[];
  /** Whether the options request is in progress. */
  isLoadingMuscleGroups?: boolean;
  /** Error from loading muscle-group options. */
  muscleGroupsError?: Error | null;
  /** Called with validated input when the form is submitted. */
  onSubmit: (input: TrainingProgramInput) => Promise<void>;
  /** Called when the user cancels. */
  onCancel: () => void;
  /** Disables controls while saving. */
  isSubmitting?: boolean;
}

interface TrainingProgramFormErrors {
  name?: string;
  objective?: string;
  muscleGroupIds?: string;
}

/**
 * Controlled form for creating and editing training programs.
 *
 * @remarks
 * Group options come from the muscle-group query, while all required-field
 * and association validation happens before invoking the parent mutation.
 * API errors are displayed directly to avoid silent failures.
 */
export function TrainingProgramForm({
  initialValue,
  muscleGroups,
  isLoadingMuscleGroups = false,
  muscleGroupsError = null,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: TrainingProgramFormProps) {
  const [name, setName] = useState(initialValue?.name ?? '');
  const [objective, setObjective] = useState(initialValue?.objective ?? '');
  const [selectedIds, setSelectedIds] = useState(initialValue?.muscleGroupIds ?? []);
  const [errors, setErrors] = useState<TrainingProgramFormErrors>({});
  const [serverError, setServerError] = useState<string>();

  /** Validates fields and submits the program and its group associations. */
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: TrainingProgramFormErrors = {};
    if (name.trim() === '') nextErrors.name = t.form.nameRequired;
    if (objective.trim() === '') nextErrors.objective = t.form.objectiveRequired;
    if (selectedIds.length === 0) {
      nextErrors.muscleGroupIds = t.form.muscleGroupsRequired;
    }
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    setServerError(undefined);
    try {
      await onSubmit({
        name: name.trim(),
        objective: objective.trim(),
        muscleGroupIds: [...selectedIds],
      });
    } catch (error) {
      if (error instanceof ApiError) {
        setServerError(error.isNetworkError() ? common.networkError : error.message);
      } else {
        setServerError(t.saveError);
      }
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      {serverError !== undefined && <Alert>{serverError}</Alert>}
      {muscleGroupsError !== null && muscleGroupsError !== undefined && (
        <Alert>
          {muscleGroupsError instanceof ApiError
            ? muscleGroupsError.message
            : t.form.muscleGroupsLoadError}
        </Alert>
      )}
      <TextField
        label={t.form.nameLabel}
        value={name}
        onChange={(event) => setName(event.target.value)}
        error={errors.name}
        placeholder={t.form.namePlaceholder}
        required
        autoFocus
        disabled={isSubmitting}
      />
      <TextField
        label={t.form.objectiveLabel}
        value={objective}
        onChange={(event) => setObjective(event.target.value)}
        error={errors.objective}
        placeholder={t.form.objectivePlaceholder}
        required
        disabled={isSubmitting}
      />
      {isLoadingMuscleGroups ? (
        <LoadingState message={t.form.muscleGroupsLoading} />
      ) : (
        <TrainingProgramMuscleGroups
          groups={muscleGroups}
          selectedIds={selectedIds}
          onChange={setSelectedIds}
          error={errors.muscleGroupIds}
          disabled={isSubmitting}
        />
      )}
      <div className={styles.actions}>
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          {common.cancel}
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {initialValue === undefined ? t.form.createButton : common.saveChanges}
        </Button>
      </div>
    </form>
  );
}
