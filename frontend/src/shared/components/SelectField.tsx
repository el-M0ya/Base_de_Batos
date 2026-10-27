import { forwardRef, type SelectHTMLAttributes } from 'react';

/**
 * Option for {@link SelectField}.
 */
export interface SelectOption {
  /** Option value. */
  value: string;
  /** Visible label. */
  label: string;
  /** Whether the option is disabled. */
  disabled?: boolean;
}

/**
 * Props for {@link SelectField}.
 */
export interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Visible label associated with the select. */
  label: string;
  /** Available options. */
  options: SelectOption[];
  /** Optional helper text shown below the select. */
  helperText?: string;
  /** Optional error message; marks the field as invalid. */
  error?: string;
}

/**
 * Accessible select field with label, helper and error text.
 */
export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(function SelectField(
  { label, options, helperText, error, id, style, ...rest },
  ref,
) {
  const selectId = id ?? `select-${label.toLowerCase().replace(/\s+/g, '-')}`;
  const hasError = Boolean(error);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
      <label
        htmlFor={selectId}
        style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-high)' }}
      >
        {label}
      </label>
      <select
        ref={ref}
        id={selectId}
        aria-invalid={hasError}
        style={{
          width: '100%',
          padding: '0.625rem 0.875rem',
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-high)',
          backgroundColor: 'var(--color-surface-inset)',
          border: `1px solid ${hasError ? 'var(--color-error)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-md)',
          outline: 'none',
          ...style,
        }}
        {...rest}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value} disabled={option.disabled}>
            {option.label}
          </option>
        ))}
      </select>
      {hasError ? (
        <span role="alert" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-error)' }}>
          {error}
        </span>
      ) : helperText ? (
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-low)' }}>{helperText}</span>
      ) : null}
    </div>
  );
});