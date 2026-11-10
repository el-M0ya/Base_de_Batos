import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { Alert } from './Alert';

describe('Alert', () => {
  it('announces errors immediately with role="alert"', () => {
    renderWithProviders(<Alert>Correo o contraseña incorrectos.</Alert>);

    expect(screen.getByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos.');
  });

  it('uses role="status" for success and info messages', () => {
    renderWithProviders(
      <>
        <Alert variant="success">Ejercicio guardado.</Alert>
        <Alert variant="info">Datos simulados.</Alert>
      </>,
    );

    expect(screen.getAllByRole('status')).toHaveLength(2);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('has no close button when onDismiss is not given', () => {
    renderWithProviders(<Alert>Error</Alert>);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('calls onDismiss when the close button is pressed', async () => {
    const onDismiss = vi.fn();
    const { user } = renderWithProviders(<Alert onDismiss={onDismiss}>Error</Alert>);

    await user.click(screen.getByRole('button', { name: 'Descartar' }));

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});
