import { type ReactNode } from 'react';

/**
 * Visual variants for {@link Alert}.
 */
export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

/**
 * Props for {@link Alert}.
 */
export interface AlertProps {
  /** Visual variant. Defaults to `info`. */
  variant?: AlertVariant;
  /** Optional title. */
  title?: string;
  /** Alert contents. */
  children: ReactNode;
}

const variantStyles: Record<AlertVariant, { bg: string; border: string; color: string }> = {
  info: { bg: 'var(--color-surface)', border: 'var(--color-border)', color: 'var(--color-text-medium)' },
  success: { bg: 'var(--color-success-surface)', border: 'var(--color-success-border)', color: 'var(--color-success)' },
  warning: { bg: 'var(--color-surface)', border: 'var(--color-warning)', color: 'var(--color-warning)' },
  error: { bg: 'var(--color-error-surface)', border: 'var(--color-error-border)', color: 'var(--color-error)' },
};

/**
 * Inline alert banner with consistent styling.
 *
 * @param props - Alert props.
 * @returns The rendered alert.
 */
export function Alert({ variant = 'info', title, children }: AlertProps): JSX.Element {
  const styles = variantStyles[variant];
  return (
    <div
      role="alert"
      style={{
        padding: 'var(--space-md)',
        borderRadius: 'var(--radius-md)',
        border: `1px solid ${styles.border}`,
        backgroundColor: styles.bg,
        color: styles.color,
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-xs)',
      }}
    >
      {title ? <strong style={{ color: 'var(--color-text-high)' }}>{title}</strong> : null}
      <span>{children}</span>
    </div>
  );
}