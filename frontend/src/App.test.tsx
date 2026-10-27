import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import App from './App';

/**
 * Smoke test ensuring the testing pipeline is wired correctly.
 */
describe('App', () => {
  it('renders the application title', () => {
    render(<App />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Planificador de Rutinas de Gimnasio',
    );
  });
});