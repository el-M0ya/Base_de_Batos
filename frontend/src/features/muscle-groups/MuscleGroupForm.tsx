import { useState, type FormEvent } from 'react';
import { ApiError } from '../../shared/api/apiError';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { TextField } from '../../shared/components/TextField';
import type { MuscleGroup, MuscleGroupInput } from '../../shared/types/muscleGroup';
import { messages } from '../../shared/i18n/messages';
import styles from './MuscleGroupForm.module.css';

const t = messages.muscleGroups;
const common = messages.common;

/** Props for the create/edit muscle-group form. */
export interface MuscleGroupFormProps {
  /** Existing record when editing; omitted for create mode. */
  initialValue?: MuscleGroup | undefined;
  /** Called with validated values when the form is submitted. */
  onSubmit: (input: MuscleGroupInput) => Promise<void>;
  /** Called when the user cancels the form. */
  onCancel: () => void;
  /** Disables controls while the mutation is pending. */
  isSubmitting?: boolean;
}

interface MuscleGroupFormErrors {
  name?: string;
  description?: string;
}

/**
 * Form used to create or edit a muscle-group catalog entry.
 *
 * @remarks
 * Required-field validation runs before the API call. Errors from the API are
 * surfaced explicitly, including server validation and network failures.
 */
export function MuscleGroupForm({
  initialValue,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: MuscleGroupFormProps) {
  const [name, setName] = useState(initialValue?.name ?? '');
  const [description, setDescription] = useState(initialValue?.description ?? '');
  const [errors, setErrors] = useState<MuscleGroupFormErrors>({});
  const [serverError, setServerError] = useState<string>();

  /** Validates required fields and reports any API error to the user. */
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: MuscleGroupFormErrors = {};
    if (name.trim() === '') nextErrors.name = t.form.nameRequired;
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    setServerError(undefined);
    try {
      await onSubmit({ name: name.trim(), description: description.trim() });
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
      <div className={styles.descriptionField}>
        <label className={styles.label} htmlFor="muscle-group-description">
          {t.form.descriptionLabel}
        </label>
        <textarea
          id="muscle-group-description"
          className={styles.textarea}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder={t.form.descriptionPlaceholder}
          rows={4}
          disabled={isSubmitting}
        />
      </div>
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
