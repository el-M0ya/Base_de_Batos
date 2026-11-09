import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { Button } from './Button';
import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('shows the title as a heading and the description', () => {
    renderWithProviders(
      <EmptyState
        title="Aún no hay ejercicios"
        description="Registra el primero para empezar a crear rutinas."
      />,
    );

    expect(screen.getByRole('heading', { name: 'Aún no hay ejercicios' })).toBeInTheDocument();
    expect(
      screen.getByText('Registra el primero para empezar a crear rutinas.'),
    ).toBeInTheDocument();
  });

  it('has no button when no action is given', () => {
    renderWithProviders(<EmptyState title="Sin resultados" />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders the action the screen passes and it works', async () => {
    const onCreate = vi.fn();
    const { user } = renderWithProviders(
      <EmptyState
        title="Aún no hay ejercicios"
        action={<Button onClick={onCreate}>Registrar ejercicio</Button>}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Registrar ejercicio' }));

    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it('hides the action when the screen passes false (e.g. user is not a trainer)', () => {
    const isTrainer = false;
    renderWithProviders(
      <EmptyState title="Aún no hay ejercicios" action={isTrainer && <Button>Registrar</Button>} />,
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
