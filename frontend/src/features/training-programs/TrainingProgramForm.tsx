import { useState, type FormEvent } from 'react';
import { ApiError } from '../../shared/api/apiError';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { LoadingState } from '../../shared/components/LoadingState';
import { TextField } from '../../shared/components/TextField';
import { TrainingProgramMuscleGroups } from './TrainingProgramMuscleGroups';
import type { MuscleGroup } from '../../shared/types/muscleGroup';
import type { TrainingProgram, TrainingProgramInput } from './types';
import styles from './TrainingProgramForm.module.css';

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
    if (name.trim() === '') nextErrors.name = 'El nombre es obligatorio.';
    if (objective.trim() === '') nextErrors.objective = 'El objetivo es obligatorio.';
    if (selectedIds.length === 0) {
      nextErrors.muscleGroupIds = 'Selecciona al menos un grupo muscular.';
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
        setServerError(
          error.isNetworkError() ? 'No se pudo conectar con el servidor.' : error.message,
        );
      } else {
        setServerError('No se pudo guardar el programa. Inténtalo nuevamente.');
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
            : 'No se pudieron cargar los grupos musculares.'}
        </Alert>
      )}
      <TextField
        label="Nombre del programa"
        value={name}
        onChange={(event) => setName(event.target.value)}
        error={errors.name}
        placeholder="Ej. Fuerza de tren superior"
        required
        autoFocus
        disabled={isSubmitting}
      />
      <TextField
        label="Objetivo"
        value={objective}
        onChange={(event) => setObjective(event.target.value)}
        error={errors.objective}
        placeholder="Ej. Mejorar la fuerza general"
        required
        disabled={isSubmitting}
      />
      {isLoadingMuscleGroups ? (
        <LoadingState message="Cargando grupos musculares…" />
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
          Cancelar
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {initialValue === undefined ? 'Crear programa' : 'Guardar cambios'}
        </Button>
      </div>
    </form>
  );
}
