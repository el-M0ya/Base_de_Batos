/**
 * Vista presentacional del formulario de usuario (E4-06).
 *
 * @remarks
 * Recibe todo por `props`: no llama a la API ni usa rutas. Renderiza los
 * campos según el rol seleccionado (entrenador: especialidad; cliente: edad y
 * sede) y muestra errores de campo y de backend. El contenedor
 * (`UserFormContainer`) provee los valores, manejadores y validación.
 */
import type { UserRole, UserFormFieldErrors } from '../../shared/types/users';
import { messages } from '../../shared/i18n/messages';
import { TextField } from '../../shared/components/TextField';
import { SelectField } from '../../shared/components/SelectField';
import { Button } from '../../shared/components/Button';

/**
 * Props de `UserFormView`.
 */
export interface UserFormViewProps {
  /** `true` si se está creando una cuenta; `false` si se está editando. */
  creating: boolean;
  /** Correo electrónico. */
  email: string;
  /** Contraseña (solicitada solo al crear). */
  password: string;
  /** Rol seleccionado. */
  role: UserRole | '';
  /** Especialidad (solo entrenador). */
  specialty: string;
  /** Edad (solo cliente). */
  age: string;
  /** Identificador de sede (solo cliente). */
  idSite: string;
  /** Errores de campo. */
  fieldErrors: UserFormFieldErrors;
  /** Error de backend o `null`. */
  backendError: string | null;
  /** `true` mientras se envía el formulario. */
  submitting: boolean;
  /** Manejador de cambio de correo. */
  onEmailChange: (value: string) => void;
  /** Manejador de cambio de contraseña. */
  onPasswordChange: (value: string) => void;
  /** Manejador de cambio de rol. */
  onRoleChange: (value: UserRole) => void;
  /** Manejador de cambio de especialidad. */
  onSpecialtyChange: (value: string) => void;
  /** Manejador de cambio de edad. */
  onAgeChange: (value: string) => void;
  /** Manejador de cambio de sede. */
  onIdSiteChange: (value: string) => void;
  /** Manejador de envío del formulario. */
  onSubmit: () => void;
  /** Manejador para cerrar el formulario. */
  onCancel: () => void;
}

/** Opciones del rol para el selector. */
const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'administrator', label: messages.users.form.roleAdministrator },
  { value: 'trainer', label: messages.users.form.roleTrainer },
  { value: 'client', label: messages.users.form.roleClient },
];

/**
 * Vista del formulario de usuario.
 */
export function UserFormView({
  creating,
  email,
  password,
  role,
  specialty,
  age,
  idSite,
  fieldErrors,
  backendError,
  submitting,
  onEmailChange,
  onPasswordChange,
  onRoleChange,
  onSpecialtyChange,
  onAgeChange,
  onIdSiteChange,
  onSubmit,
  onCancel,
}: UserFormViewProps) {
  return (
    <section className="user-form">
      <h1 className="user-form__title">
        {creating ? messages.users.form.createTitle : messages.users.form.editTitle}
      </h1>

      {backendError && (
        <div className="user-form__backend-error" role="alert">
          {backendError}
        </div>
      )}

      <form onSubmit={(event: React.FormEvent) => {
        event.preventDefault();
        void onSubmit();
      }}>
        <TextField
          label={messages.users.form.emailLabel}
          placeholder={messages.users.form.emailPlaceholder}
          value={email}
          onChange={(event) => onEmailChange(event.target.value)}
          error={fieldErrors.email}
          required
        />

        {creating && (
          <TextField
            label={messages.users.form.passwordLabel}
            placeholder={messages.users.form.passwordPlaceholder}
            type="password"
            value={password}
            onChange={(event) => onPasswordChange(event.target.value)}
            error={fieldErrors.password}
            required
          />
        )}

        <SelectField
          label={messages.users.form.roleLabel}
          options={ROLE_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
          value={role}
          onChange={(event) => onRoleChange(event.target.value as UserRole)}
          error={fieldErrors.role}
          required
          placeholder={messages.users.form.roleSelect}
        />

        {role === 'trainer' && (
          <TextField
            label={messages.users.form.specialtyLabel}
            placeholder={messages.users.form.specialtyPlaceholder}
            value={specialty}
            onChange={(event) => onSpecialtyChange(event.target.value)}
            error={fieldErrors.specialty}
          />
        )}

        {role === 'client' && (
          <>
            <TextField
              label={messages.users.form.ageLabel}
              type="number"
              value={age}
              onChange={(event) => onAgeChange(event.target.value)}
              error={fieldErrors.age}
            />
            <TextField
              label={messages.users.form.siteLabel}
              type="number"
              value={idSite}
              onChange={(event) => onIdSiteChange(event.target.value)}
              error={fieldErrors.idSite}
            />
          </>
        )}

        <div className="user-form__actions">
          <Button variant="primary" type="submit" disabled={submitting}>
            {creating
              ? messages.users.form.createButton
              : messages.users.form.saveButton}
          </Button>
          <Button variant="secondary" type="button" onClick={onCancel}>
            {messages.users.form.cancelButton}
          </Button>
        </div>
      </form>
    </section>
  );
}
