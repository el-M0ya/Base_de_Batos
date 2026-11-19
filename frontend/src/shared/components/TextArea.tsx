import { useId, type TextareaHTMLAttributes } from 'react';
import styles from './TextArea.module.css';

/**
 * Props of the multi-line text field.
 *
 * @remarks
 * Extends the native `<textarea>` props (`value`, `onChange`, `rows`,
 * `placeholder`, `readOnly`...), so it accepts everything a textarea does.
 * Same `label` / `error` / `hint` contract as `TextField`.
 */
export interface TextAreaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'id'> {
  /** Visible label. Required: every field must have one for accessibility. */
  label: string;
  /** Error message. When present, the field is marked as invalid. */
  error?: string | undefined;
  /** Help text shown below the field when there is no error. */
  hint?: string | undefined;
}

/**
 * Labelled multi-line text field of the FORJA design system.
 *
 * @remarks
 * The multi-line counterpart of `TextField`: it links the label, hint and
 * error to the textarea for screen readers, and shares its styles.
 *
 * @example
 * ```tsx
 * <TextArea
 *   label="Descripción"
 *   value={description}
 *   onChange={(event) => setDescription(event.target.value)}
 *   rows={4}
 * />
 * ```
 */
export function TextArea({ label, error, hint, rows = 4, className, ...rest }: TextAreaProps) {
  // Unique ids so the label and messages are linked to THIS textarea.
  const textareaId = useId();
  const messageId = `${textareaId}-message`;

  const hasError = error !== undefined && error !== '';
  const message = hasError ? error : hint;

  const textareaClasses = [styles.textarea, hasError ? styles.invalid : '']
    .filter(Boolean)
    .join(' ');

  return (
    <div className={[styles.field, className ?? ''].filter(Boolean).join(' ')}>
      <label className={styles.label} htmlFor={textareaId}>
        {label}
      </label>

      <textarea
        {...rest}
        id={textareaId}
        rows={rows}
        className={textareaClasses}
        aria-invalid={hasError || undefined}
        aria-describedby={message !== undefined ? messageId : undefined}
      />

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
