import { messages } from '../i18n/messages';
import styles from './LoadingState.module.css';

/** Props of the loading state. */
export interface LoadingStateProps {
  /** Text under the spinner. Defaults to "Cargando…". */
  message?: string | undefined;
}

/**
 * Placeholder shown while a screen waits for its data.
 *
 * @remarks
 * Uses `role="status"` so screen readers announce the message politely;
 * the spinner is decorative and hidden from them.
 *
 * @example
 * ```tsx
 * if (isLoading) return <LoadingState message="Cargando ejercicios…" />;
 * ```
 */
export function LoadingState({ message = messages.states.loading }: LoadingStateProps) {
  return (
    <div className={styles.container} role="status">
      <span className={styles.spinner} aria-hidden="true" />
      <p className={styles.message}>{message}</p>
    </div>
  );
}
