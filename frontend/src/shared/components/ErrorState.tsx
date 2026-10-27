import { type ReactNode } from 'react';
import { messages } from '../i18n/messages';

/**
 * Props for {@link ErrorState}.
 */
export interface ErrorStateProps {
  /** Optional title. */
  title?: string;
  /** Optional description. */
  description?: string;
  /** Optional retry handler. */
  onRetry?: () => void;
  /** Optional retry label. */
  retryLabel?: string;
  /** Optional extra content. */
  children?: ReactNode;
}

/**
 * Centered error placeholder with optional retry action.
 *
 * @param props - Error state props.
 * @returns The rendered error state.
 */
export function ErrorState({
  title = messages.states.errorTitle,
  description = messages.states.errorDescription,
  onRetry,
  retryLabel = messages.common.retry,
  children,
}: ErrorStateProps): JSX.Element {
  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--space-sm)',
        padding: 'var(--space-xl)',
        textAlign: 'center',
        color: 'var(--color-text-medium)',
      }}
    >
      <strong style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-lg)' }}>{title}</strong>
      <span style={{ fontSize: 'var(--font-size-sm)' }}>{description}</span>
      {children}
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          style={{
            marginTop: 'var(--space-sm)',
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface-elevated)',
            color: 'var(--color-text-high)',
            cursor: 'pointer',
          }}
        >
          {retryLabel}
        </button>
      ) : null}
    </div>
  );
}