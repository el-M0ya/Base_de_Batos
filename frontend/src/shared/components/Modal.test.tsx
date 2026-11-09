import { describe, expect, it, vi } from 'vitest';
import { fireEvent, renderWithProviders, screen } from '../../test/test-utils';
import { Button } from './Button';
import { Modal } from './Modal';

function renderModal(props: Partial<Parameters<typeof Modal>[0]> = {}) {
  const onClose = vi.fn();
  const result = renderWithProviders(
    <Modal isOpen onClose={onClose} title="Eliminar ejercicio" {...props}>
      Esta acción no se puede deshacer.
    </Modal>,
  );
  return { onClose, ...result };
}

describe('Modal', () => {
  it('shows nothing while closed', () => {
    renderModal({ isOpen: false });

    expect(screen.queryByText('Esta acción no se puede deshacer.')).not.toBeInTheDocument();
  });

  it('opens as a dialog named by its title', () => {
    renderModal();

    expect(screen.getByRole('dialog', { name: 'Eliminar ejercicio' })).toBeInTheDocument();
    expect(screen.getByText('Esta acción no se puede deshacer.')).toBeInTheDocument();
  });

  it('calls onClose from the close button', async () => {
    const { onClose, user } = renderModal();

    await user.click(screen.getByRole('button', { name: 'Cerrar' }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape fires the "cancel" event', () => {
    const { onClose } = renderModal();

    fireEvent(screen.getByRole('dialog'), new Event('cancel', { cancelable: true }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes on a backdrop click but not on a click inside the content', async () => {
    const { onClose, user } = renderModal();

    await user.click(screen.getByText('Esta acción no se puede deshacer.'));
    expect(onClose).not.toHaveBeenCalled();

    await user.click(screen.getByRole('dialog'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('ignores backdrop clicks when closeOnBackdropClick is false', async () => {
    const { onClose, user } = renderModal({ closeOnBackdropClick: false });

    await user.click(screen.getByRole('dialog'));

    expect(onClose).not.toHaveBeenCalled();
  });

  it('renders the footer buttons it receives', () => {
    renderModal({ footer: <Button>Eliminar</Button> });

    expect(screen.getByRole('button', { name: 'Eliminar' })).toBeInTheDocument();
  });
});
