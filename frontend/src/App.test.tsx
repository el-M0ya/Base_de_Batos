import { describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from './test/test-utils';
import { App } from './App';

describe('App', () => {
  it('shows the login screen', () => {
    renderWithProviders(<App />);

    expect(screen.getByRole('heading', { level: 1, name: 'Inicia sesión' })).toBeInTheDocument();
  });
});
