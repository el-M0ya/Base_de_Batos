import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';

/**
 * Props for {@link TextField}.
 */
export interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Visible label associated with the input. */
  label: string;
  /** Optional helper text shown below the input. */
  helperText?: string;
  /** Optional error message; marks the field as invalid. */
  error?: string;
  /** Optional leading icon/element. */
  leading?: ReactNode;
}

/**
 * Accessible text input with label, helper and error text.
 */
export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, helperText, error, leading, id, style, ...rest },
  ref,
) {
  const inputId = id ?? `field-${label.toLowerCase().replace(/\s+/g, '-')}`;
  const hasError = Boolean(error);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
      <label
        htmlFor={inputId}
        style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-high)' }}
      >
        {label}
      </label>
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        {leading ? (
          <span style={{ position: 'absolute', left: 'var(--space-sm)', color: 'var(--color-text-low)' }} aria-hidden="true">
            {leading}
          </span>
        ) : null}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={hasError}
          aria-describedby={hasError ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
          style={{
            width: '100%',
            padding: '0.625rem 0.875rem',
            paddingLeft: leading ? '2.25rem' : '0.875rem',
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-high)',
            backgroundColor: 'var(--color-surface-inset)',
            border: `1px solid ${hasError ? 'var(--color-error)' : 'var(--color-border)'}`,
            borderRadius: 'var(--radius-md)',
            outline: 'none',
            ...style,
          }}
          {...rest}
        />
      </div>
      {hasError ? (
        <span id={`${inputId}-error`} role="alert" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-error)' }}>
          {error}
        </span>
      ) : helperText ? (
        <span id={`${inputId}-helper`} style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-low)' }}>
          {helperText}
        </span>
      ) : null}
    </div>
  );
});