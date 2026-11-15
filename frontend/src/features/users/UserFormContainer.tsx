/**
 * Contenedor del formulario de creación de usuarios (E4-06).
 *
 * @remarks
 * Orquesta `useUserForm` (validación) y `useUsers` (creación) con
 * `UserFormView` (presentación). Solo se usa para crear cuentas nuevas; la
 * edición simple se hace desde `UsersContainer`.
 */
import { useState } from 'react';
import { useUserForm } from './useUserForm';
import { useUsers } from './useUsers';
import { UserFormView } from './UserFormView';
import type { CreateUserInput } from '../../shared/types/users';
import { messages } from '../../shared/i18n/messages';

/**
 * Contenedor del formulario de creación de usuarios.
 *
 * @remarks
 * Valida los datos antes de enviar al backend y muestra los errores del
 * backend (por ejemplo, correo duplicado) gracias a `setBackendError`.
 */
export function UserFormContainer({
  onCancel,
}: {
  /** Manejador para cerrar el formulario. */
  onCancel: () => void;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [values, setValues] = useState<CreateUserInput>({
    email: '',
    password: '',
    role: 'client',
  } as CreateUserInput);
  const { fieldErrors, backendError, setBackendError, validateCreate, clearErrors } = useUserForm();
  const { createUser, loading } = useUsers();

  const isCreating = loading || submitting;

  function handleFieldChange(field: keyof CreateUserInput, value: string) {
    setValues((prev: CreateUserInput) => {
      const next = { ...prev } as Record<string, unknown>;
      if (field === 'age' || field === 'idSite') {
        next[field] = value === '' ? undefined : Number(value);
      } else {
        next[field] = value;
      }
      return next as unknown as CreateUserInput;
    });
    setBackendError(null);
  }

  function handleRoleChange(value: string) {
    setValues((prev: CreateUserInput) => ({
      ...prev,
      role: value as CreateUserInput['role'],
    }));
    setBackendError(null);
  }

  async function handleSubmit() {
    clearErrors();
    if (!validateCreate(values)) {
      return;
    }

    setSubmitting(true);
    try {
      const created = await createUser(values);
      if (created) {
        setValues({
          email: '',
          password: '',
          role: 'client',
        } as CreateUserInput);
        onCancel();
      }
    } catch {
      setBackendError(messages.users.errors.createFailed);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <UserFormView
      creating
      email={values.email}
      password={values.password}
      role={values.role}
      specialty={values.specialty ?? ''}
      age={String(values.age ?? '')}
      idSite={String(values.idSite ?? '')}
      fieldErrors={fieldErrors}
      backendError={backendError}
      submitting={isCreating}
      onEmailChange={(value) => void handleFieldChange('email', value)}
      onPasswordChange={(value) => void handleFieldChange('password', value)}
      onRoleChange={handleRoleChange}
      onSpecialtyChange={(value) => void handleFieldChange('specialty', value)}
      onAgeChange={(value) => void handleFieldChange('age', value)}
      onIdSiteChange={(value) => void handleFieldChange('idSite', value)}
      onSubmit={handleSubmit}
      onCancel={onCancel}
    />
  );
}
