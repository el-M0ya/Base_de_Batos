import { messages } from '../i18n/messages';

/**
 * Props for {@link LoadingState}.
 */
export interface LoadingStateProps {
  /** Optional title. */
  title?: string;
  /** Optional description. */
  description?: string;
}

/**
 * Centered loading indicator with optional text.
 *
 * @param props - Loading state props.
 * @returns The rendered loading state.
 */
export function LoadingState({
  title = messages.states.loadingTitle,
  description = messages.states.loadingDescription,
}: LoadingStateProps): JSX.Element {
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--space-sm)',
        padding: 'var(--space-xl)',
        color: 'var(--color-text-medium)',
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: '2rem',
          height: '2rem',
          border: '3px solid var(--color-border)',
          borderTopColor: 'var(--color-primary)',
          borderRadius: 'var(--radius-full)',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      <strong style={{ color: 'var(--color-text-high)' }}>{title}</strong>
      <span style={{ fontSize: 'var(--font-size-sm)' }}>{description}</span>
    </div>
  );
}