import { describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from './test/test-utils';
import { App } from './App';

describe('App', () => {
  it('renderiza el application shell con encabezado y botón de cierre de sesión', () => {
    renderWithProviders(<App />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Base de Batos' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Cerrar sesión' }),
    ).toBeInTheDocument();
  });
});
