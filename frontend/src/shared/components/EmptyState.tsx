import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import styles from './EmptyState.module.css';

/** Props of the empty state. */
export interface EmptyStateProps {
  /** What is missing, e.g. "Aún no hay ejercicios". */
  title: string;
  /** Why it is empty or what to do next. */
  description?: string | undefined;
  /** Icon shown above the title. Defaults to an empty inbox. */
  icon?: ReactNode;
  /**
   * Optional element to solve the situation, usually a `Button`.
   * The screen decides whether to pass it (e.g. only for trainers).
   */
  action?: ReactNode;
}

/**
 * Message shown when a list or report loaded correctly but has no data.
 *
 * @remarks
 * Prevents an empty table, which would not explain anything to the user.
 *
 * @example
 * ```tsx
 * <EmptyState
 *   title="Aún no hay ejercicios"
 *   description="Registra el primero para empezar a crear rutinas."
 *   action={canCreate && <Button onClick={openForm}>Registrar ejercicio</Button>}
 * />
 * ```
 */
export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <section className={styles.container}>
      <span className={styles.iconBox} aria-hidden="true">
        {icon ?? <Inbox size={24} />}
      </span>

      <h2 className={styles.title}>{title}</h2>

      {description !== undefined && <p className={styles.description}>{description}</p>}

      {action !== undefined && action !== null && action !== false && (
        <div className={styles.action}>{action}</div>
      )}
    </section>
  );
}
