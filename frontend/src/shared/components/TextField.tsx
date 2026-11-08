import { useId, useState, type InputHTMLAttributes, type ReactNode } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { messages } from '../i18n/messages';
import styles from './TextField.module.css';

/**
 * Props of the text field.
 *
 * @remarks
 * Extends the native `<input>` props (`value`, `onChange`, `type`, `required`,
 * `placeholder`, `autoComplete`...), so it accepts everything an input does.
 */
export interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  /** Visible label. Required: every field must have one for accessibility. */
  label: string;
  /** Error message. When present, the field is marked as invalid. */
  error?: string;
  /** Help text shown below the field when there is no error. */
  hint?: string;
  /** Optional icon shown at the start of the field (e.g. a mail icon). */
  icon?: ReactNode;
}

/**
 * Labelled text field of the FORJA design system.
 *
 * @remarks
 * Links the label, hint and error to the input for screen readers.
 * With `type="password"` it adds a button to show or hide the password.
 *
 * @example
 * ```tsx
 * <TextField label="Correo electrónico" type="email" icon={<Mail />} error={emailError} />
 * ```
 */
export function TextField({
  label,
  error,
  hint,
  icon,
  type = 'text',
  className,
  ...rest
}: TextFieldProps) {
  // Unique ids so the label and messages are linked to THIS input.
  const inputId = useId();
  const messageId = `${inputId}-message`;

  // State: whether the password is currently visible.
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const isPassword = type === 'password';
  const effectiveType = isPassword && isPasswordVisible ? 'text' : type;
  const hasError = error !== undefined && error !== '';
  const message = hasError ? error : hint;

  const inputClasses = [
    styles.input,
    icon !== undefined ? styles.withIcon : '',
    isPassword ? styles.withToggle : '',
    hasError ? styles.invalid : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={[styles.field, className ?? ''].filter(Boolean).join(' ')}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>

      <div className={styles.control}>
        {icon !== undefined && (
          <span className={styles.icon} aria-hidden="true">
            {icon}
          </span>
        )}

        <input
          {...rest}
          id={inputId}
          type={effectiveType}
          className={inputClasses}
          aria-invalid={hasError || undefined}
          aria-describedby={message !== undefined ? messageId : undefined}
        />

        {isPassword && (
          <button
            type="button"
            className={styles.toggle}
            onClick={() => setIsPasswordVisible((visible) => !visible)}
            aria-label={
              isPasswordVisible ? messages.textField.hidePassword : messages.textField.showPassword
            }
            aria-pressed={isPasswordVisible}
          >
            {isPasswordVisible ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>

      {message !== undefined && (
        // role="alert" makes screen readers announce the error as soon as it appears.
        <p
          id={messageId}
          className={hasError ? styles.error : styles.hint}
          role={hasError ? 'alert' : undefined}
        >
          {message}
        </p>
      )}
    </div>
  );
}
