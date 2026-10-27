import { useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

/**
 * Props for {@link Modal}.
 */
export interface ModalProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Called when the modal requests to close. */
  onClose: () => void;
  /** Modal title. */
  title?: string;
  /** Modal contents. */
  children: ReactNode;
  /** Optional footer content. */
  footer?: ReactNode;
}

/**
 * Accessible modal dialog rendered through a portal.
 *
 * @param props - Modal props.
 * @returns The rendered modal or `null` when closed.
 */
export function Modal({ open, onClose, title, children, footer }: ModalProps): JSX.Element | null {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handler);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      role="presentation"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-md)',
        zIndex: 50,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '32rem',
          backgroundColor: 'var(--color-surface-elevated)',
          border: '1px solid var(--color-border-strong)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-modal)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {title ? (
          <header
            style={{
              padding: 'var(--space-md) var(--space-lg)',
              borderBottom: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <h2 style={{ fontSize: 'var(--font-size-lg)' }}>{title}</h2>
            <button
              type="button"
              onClick={onClose}
              aria-label="Cerrar ventana"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--color-text-medium)',
                cursor: 'pointer',
                fontSize: 'var(--font-size-lg)',
              }}
            >
              ×
            </button>
          </header>
        ) : null}
        <div style={{ padding: 'var(--space-lg)' }}>{children}</div>
        {footer ? (
          <footer
            style={{
              padding: 'var(--space-md) var(--space-lg)',
              borderTop: '1px solid var(--color-border)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 'var(--space-sm)',
            }}
          >
            {footer}
          </footer>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}