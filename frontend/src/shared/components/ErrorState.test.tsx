import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { ErrorState } from './ErrorState';

describe('ErrorState', () => {
  it('announces the default friendly message', () => {
    renderWithProviders(<ErrorState />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('No se pudieron cargar los datos');
    expect(alert).toHaveTextContent('Comprueba tu conexión e inténtalo de nuevo.');
  });

  it('shows a custom title and description', () => {
    renderWithProviders(
      <ErrorState title="No se pudo cargar el reporte" description="Inténtalo más tarde." />,
    );

    expect(
      screen.getByRole('heading', { name: 'No se pudo cargar el reporte' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Inténtalo más tarde.')).toBeInTheDocument();
  });

  it('has no retry button when onRetry is not given', () => {
    renderWithProviders(<ErrorState />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('calls onRetry when "Reintentar" is pressed', async () => {
    const onRetry = vi.fn();
    const { user } = renderWithProviders(<ErrorState onRetry={onRetry} />);

    await user.click(screen.getByRole('button', { name: 'Reintentar' }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('disables the button while retrying', () => {
    renderWithProviders(<ErrorState onRetry={vi.fn()} isRetrying />);

    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeDisabled();
  });
});
