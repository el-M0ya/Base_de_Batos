import { useState, type FormEvent } from 'react';
import { ApiError } from '../../shared/api/apiError';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { TextField } from '../../shared/components/TextField';
import { messages } from '../../shared/i18n/messages';
import type { Site, SiteInput } from './types';
import styles from './SiteForm.module.css';

const t = messages.sites;
const common = messages.common;

/** Props for the create/edit site form. */
export interface SiteFormProps {
  /** Existing site when editing; omitted in create mode. */
  initialValue?: Site | undefined;
  /** Called after local validation with the submitted values. */
  onSubmit: (input: SiteInput) => Promise<void>;
  /** Called when the user cancels the form. */
  onCancel: () => void;
  /** Disables controls while the mutation is pending. */
  isSubmitting?: boolean;
}

interface SiteFormErrors {
  name?: string;
  address?: string;
}

/**
 * Controlled form for creating and editing gym sites.
 *
 * @remarks
 * Both fields are required by the database constraints. Server and network
 * failures are converted to visible messages without being swallowed.
 */
export function SiteForm({
  initialValue,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: SiteFormProps) {
  const [name, setName] = useState(initialValue?.name ?? '');
  const [address, setAddress] = useState(initialValue?.address ?? '');
  const [errors, setErrors] = useState<SiteFormErrors>({});
  const [serverError, setServerError] = useState<string>();

  /** Validates required fields and submits the site to the parent view. */
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: SiteFormErrors = {};
    if (name.trim() === '') nextErrors.name = t.form.nameRequired;
    if (address.trim() === '') nextErrors.address = t.form.addressRequired;
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    setServerError(undefined);
    try {
      await onSubmit({ name: name.trim(), address: address.trim() });
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
      <TextField
        label={t.form.addressLabel}
        value={address}
        onChange={(event) => setAddress(event.target.value)}
        error={errors.address}
        placeholder={t.form.addressPlaceholder}
        required
        disabled={isSubmitting}
      />
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
