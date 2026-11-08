import type { ReactNode } from 'react';
import { CircleAlert, CircleCheck, Info, X } from 'lucide-react';
import { messages } from '../i18n/messages';
import styles from './Alert.module.css';

/** Kind of message the alert shows. */
export type AlertVariant = 'error' | 'success' | 'info';

/** Props of the alert. */
export interface AlertProps {
  /** Kind of message. Defaults to `error`. */
  variant?: AlertVariant;
  /** Message text. */
  children: ReactNode;
  /**
   * Called when the user presses the close button.
   * If omitted, the alert has no close button.
   */
  onDismiss?: () => void;
}

// Each variant has its own icon, so the meaning does not rely on color alone.
const icons: Record<AlertVariant, ReactNode> = {
  error: <CircleAlert size={18} />,
  success: <CircleCheck size={18} />,
  info: <Info size={18} />,
};

/**
 * Inline message box of the FORJA design system (e.g. "Correo o contraseña incorrectos").
 *
 * @remarks
 * Errors use `role="alert"` so screen readers announce them immediately;
 * success and info use `role="status"`, which waits for a pause.
 *
 * @example
 * ```tsx
 * {loginError && <Alert onDismiss={() => setLoginError(null)}>{loginError}</Alert>}
 * ```
 */
export function Alert({ variant = 'error', children, onDismiss }: AlertProps) {
  return (
    <div
      className={`${styles.alert} ${styles[variant]}`}
      role={variant === 'error' ? 'alert' : 'status'}
    >
      <span className={styles.icon} aria-hidden="true">
        {icons[variant]}
      </span>

      <div className={styles.message}>{children}</div>

      {onDismiss !== undefined && (
        <button
          type="button"
          className={styles.dismiss}
          onClick={onDismiss}
          aria-label={messages.alert.dismiss}
          title={messages.alert.dismiss}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}
