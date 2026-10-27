import { type ReactNode } from 'react';
import { messages } from '../i18n/messages';

/**
 * Props for {@link EmptyState}.
 */
export interface EmptyStateProps {
  /** Optional title. */
  title?: string;
  /** Optional description. */
  description?: string;
  /** Optional action element (e.g. a button). */
  action?: ReactNode;
}

/**
 * Centered empty-result placeholder.
 *
 * @param props - Empty state props.
 * @returns The rendered empty state.
 */
export function EmptyState({
  title = messages.states.emptyTitle,
  description = messages.states.emptyDescription,
  action,
}: EmptyStateProps): JSX.Element {
  return (
    <div
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
      <strong style={{ color: 'var(--color-text-high)', fontSize: 'var(--font-size-lg)' }}>{title}</strong>
      <span style={{ fontSize: 'var(--font-size-sm)' }}>{description}</span>
      {action ? <div style={{ marginTop: 'var(--space-sm)' }}>{action}</div> : null}
    </div>
  );
}