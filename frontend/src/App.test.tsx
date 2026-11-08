import { describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from './test/test-utils';
import { App } from './App';

describe('App', () => {
  it('muestra el nombre del sistema', () => {
    renderWithProviders(<App />);

    expect(screen.getByRole('heading', { level: 1, name: 'Base de Batos' })).toBeInTheDocument();
  });
});
