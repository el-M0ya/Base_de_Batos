import {
  useEffect,
  useId,
  useRef,
  type MouseEvent,
  type ReactNode,
  type SyntheticEvent,
} from 'react';
import { X } from 'lucide-react';
import { messages } from '../i18n/messages';
import styles from './Modal.module.css';

/** Props of the modal. */
export interface ModalProps {
  /** Whether the modal is open. The screen owns this state. */
  isOpen: boolean;
  /** Called when the user asks to close it (✕, Escape or click outside). */
  onClose: () => void;
  /** Title shown at the top; also the name screen readers announce. */
  title: string;
  /** Content of the modal (text, a form...). */
  children: ReactNode;
  /** Optional buttons at the bottom, e.g. "Cancelar" and "Guardar". */
  footer?: ReactNode;
  /** Close when clicking the dark area outside. Defaults to true. */
  closeOnBackdropClick?: boolean | undefined;
}

/**
 * Dialog window over the page, built on the native `<dialog>` element.
 *
 * @remarks
 * `showModal()` gives us, for free: the dark backdrop, focus moved inside
 * and trapped there, Escape to close, and focus returned to the opener.
 * The modal never closes by itself: it calls `onClose` and the screen
 * decides by setting `isOpen` to false.
 *
 * @example
 * ```tsx
 * <Modal
 *   isOpen={isConfirmOpen}
 *   onClose={() => setIsConfirmOpen(false)}
 *   title="Eliminar ejercicio"
 *   footer={<Button onClick={remove}>Eliminar</Button>}
 * >
 *   Esta acción no se puede deshacer.
 * </Modal>
 * ```
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  closeOnBackdropClick = true,
}: ModalProps) {
  // A handle to the real <dialog> element, to call showModal() and close().
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  // Keep the real dialog in sync with the `isOpen` prop.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog === null) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  // Escape fires a "cancel" event. We stop the browser from closing the
  // dialog on its own and let the screen decide through onClose.
  function handleCancel(event: SyntheticEvent<HTMLDialogElement>) {
    event.preventDefault();
    onClose();
  }

  // A click on the dark backdrop is reported with the <dialog> itself as
  // target; clicks on the content have an inner element as target.
  function handleClick(event: MouseEvent<HTMLDialogElement>) {
    if (closeOnBackdropClick && event.target === dialogRef.current) {
      onClose();
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className={styles.dialog}
      aria-labelledby={titleId}
      onCancel={handleCancel}
      onClick={handleClick}
    >
      {/* Content is only rendered while open, so closed modals cost nothing. */}
      {isOpen && (
        <div className={styles.panel}>
          <header className={styles.header}>
            <h2 id={titleId} className={styles.title}>
              {title}
            </h2>
            <button
              type="button"
              className={styles.close}
              onClick={onClose}
              aria-label={messages.modal.close}
              title={messages.modal.close}
            >
              <X size={18} />
            </button>
          </header>

          <div className={styles.body}>{children}</div>

          {footer !== undefined && <footer className={styles.footer}>{footer}</footer>}
        </div>
      )}
    </dialog>
  );
}
