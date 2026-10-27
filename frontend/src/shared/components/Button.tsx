import { type ButtonHTMLAttributes, type ReactNode } from 'react';

/**
 * Visual variants supported by {@link Button}.
 */
export type ButtonVariant = 'primary' | 'secondary' | 'ghost';

/**
 * Size variants supported by {@link Button}.
 */
export type ButtonSize = 'sm' | 'md' | 'lg';

/**
 * Props for {@link Button}.
 */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant. Defaults to `primary`. */
  variant?: ButtonVariant;
  /** Size variant. Defaults to `md`. */
  size?: ButtonSize;
  /** Button contents. */
  children: ReactNode;
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: 'var(--color-primary)',
    color: 'var(--color-text-on-primary)',
    border: '1px solid var(--color-primary)',
  },
  secondary: {
    backgroundColor: 'var(--color-surface-elevated)',
    color: 'var(--color-text-high)',
    border: '1px solid var(--color-border)',
  },
  ghost: {
    backgroundColor: 'transparent',
    color: 'var(--color-text-medium)',
    border: '1px solid transparent',
  },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: { padding: '0.375rem 0.75rem', fontSize: 'var(--font-size-sm)' },
  md: { padding: '0.625rem 1.25rem', fontSize: 'var(--font-size-md)' },
  lg: { padding: '0.875rem 1.75rem', fontSize: 'var(--font-size-lg)' },
};

/**
 * Accessible button with consistent styling and focus ring.
 *
 * @param props - Button props.
 * @returns The rendered button.
 */
export function Button({
  variant = 'primary',
  size = 'md',
  children,
  style,
  disabled,
  ...rest
}: ButtonProps): JSX.Element {
  return (
    <button
      type="button"
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--space-sm)',
        borderRadius: 'var(--radius-md)',
        fontWeight: 'var(--font-weight-bold)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'background-color 150ms ease, border-color 150ms ease, color 150ms ease',
        ...variantStyles[variant],
        ...sizeStyles[size],
        ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}