import { describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { LoadingState } from './LoadingState';

describe('LoadingState', () => {
  it('announces the default message to screen readers', () => {
    renderWithProviders(<LoadingState />);

    expect(screen.getByRole('status')).toHaveTextContent('Cargando…');
  });

  it('shows a custom message', () => {
    renderWithProviders(<LoadingState message="Cargando ejercicios…" />);

    expect(screen.getByRole('status')).toHaveTextContent('Cargando ejercicios…');
  });
});
