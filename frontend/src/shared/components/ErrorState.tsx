import { CloudOff, RotateCw } from 'lucide-react';
import { messages } from '../i18n/messages';
import { Button } from './Button';
import styles from './ErrorState.module.css';

/** Props of the error state. */
export interface ErrorStateProps {
  /** Short explanation. Defaults to "No se pudieron cargar los datos". */
  title?: string | undefined;
  /** What the user can do. Defaults to "Comprueba tu conexión…". */
  description?: string | undefined;
  /** Called when the user presses "Reintentar". Without it, no button is shown. */
  onRetry?: (() => void) | undefined;
  /** True while the retry is in progress: the button shows a spinner. */
  isRetrying?: boolean | undefined;
}

/**
 * Shown INSTEAD of a screen's content when its data could not be loaded.
 *
 * @remarks
 * Shows a friendly message, never technical details (status codes, stack
 * traces): those belong in the console. Uses `role="alert"` so screen
 * readers announce the failure.
 *
 * @example
 * ```tsx
 * if (isError) return <ErrorState onRetry={refetch} isRetrying={isFetching} />;
 * ```
 */
export function ErrorState({
  title = messages.states.errorTitle,
  description = messages.states.errorDescription,
  onRetry,
  isRetrying = false,
}: ErrorStateProps) {
  return (
    <section className={styles.container} role="alert">
      <span className={styles.iconBox} aria-hidden="true">
        <CloudOff size={24} />
      </span>

      <h2 className={styles.title}>{title}</h2>
      <p className={styles.description}>{description}</p>

      {onRetry !== undefined && (
        <div className={styles.action}>
          <Button
            variant="secondary"
            onClick={onRetry}
            isLoading={isRetrying}
            icon={<RotateCw size={16} />}
          >
            {messages.states.retry}
          </Button>
        </div>
      )}
    </section>
  );
}
