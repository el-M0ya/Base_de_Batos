



import { useId, type ReactNode, type SelectHTMLAttributes } from 'react';
import { ChevronDown } from 'lucide-react';
import styles from './SelectField.module.css';

/** One choice of the select. */
export interface SelectOption {
  /** Value sent with the form (e.g. a database id). */
  value: string;
  /** Text the user sees. */
  label: string;
}

/**
 * Props of the select field.
 *
 * @remarks
 * Extends the native `<select>` props (`value`, `onChange`, `required`,
 * `disabled`...), so it accepts everything a select does.
 */
export interface SelectFieldProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  /** Visible label. Required for accessibility. */
  label: string;
  /** Choices to show, in order. */
  options: readonly SelectOption[];
  /** Text shown while nothing is selected (e.g. "Selecciona tu sede"). */
  placeholder?: string | undefined;
  /** Error message. When present, the field is marked as invalid. */
  error?: string | undefined;
  /** Help text shown below the field when there is no error. */
  hint?: string | undefined;
  /** Optional icon shown at the start of the field. */
  icon?: ReactNode;
}

/**
 * Labelled select of the FORJA design system, built on the native `<select>`
 * so keyboard, screen readers and mobile pickers work out of the box.
 *
 * @example
 * ```tsx
 * <SelectField
 *   label="Sede de entrenamiento"
 *   placeholder="Selecciona tu sede preferida"
 *   icon={<MapPin />}
 *   options={sites}
 *   value={siteId}
 *   onChange={(event) => setSiteId(event.target.value)}
 * />
 * ```
 */
export function SelectField({
  label,
  options,
  placeholder,
  error,
  hint,
  icon,
  className,
  ...rest
}: SelectFieldProps) {
  const selectId = useId();
  const messageId = `${selectId}-message`;

  const hasError = error !== undefined && error !== '';
  const message = hasError ? error : hint;

  const selectClasses = [
    styles.select,
    icon !== undefined ? styles.withIcon : '',
    hasError ? styles.invalid : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={[styles.field, className ?? ''].filter(Boolean).join(' ')}>
      <label className={styles.label} htmlFor={selectId}>
        {label}
      </label>

      <div className={styles.control}>
        {icon !== undefined && (
          <span className={styles.icon} aria-hidden="true">
            {icon}
          </span>
        )}

        <select
          {...rest}
          id={selectId}
          className={selectClasses}
          aria-invalid={hasError || undefined}
          aria-describedby={message !== undefined ? messageId : undefined}
        >
          {placeholder !== undefined && (
            // Disabled: the user can see it but cannot pick it back once a choice is made.
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            // `key` lets React tell the options apart when the list changes.
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <span className={styles.chevron} aria-hidden="true">
          <ChevronDown size={18} />
        </span>
      </div>

      {message !== undefined && (
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
