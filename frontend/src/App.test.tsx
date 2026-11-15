import { afterEach, describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from './test/test-utils';
import { App } from './App';

/** Stores an administrator session, as the login would after a successful sign-in. */
function signInAsAdmin() {
  sessionStorage.setItem('forjafit:token', 'demo:admin@forjafit.demo');
  sessionStorage.setItem(
    'forjafit:user',
    JSON.stringify({
      id: 'user-admin@forjafit.demo',
      email: 'admin@forjafit.demo',
      role: 'administrator',
      capabilities: { can_generate: false, can_validate: false },
    }),
  );
}

afterEach(() => {
  sessionStorage.clear();
  window.history.pushState({}, '', '/');
});

describe('App', () => {
  it('renderiza el application shell con encabezado y botón de cierre de sesión', () => {
    renderWithProviders(<App />);

    expect(screen.getByRole('heading', { level: 1, name: 'Base de Batos' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument();
  });

  // Regression: pages that use TanStack Query need the global QueryClientProvider.
  // Without it, /exercises threw "No QueryClient set" and the whole app went blank.
  it('muestra la página de ejercicios gracias al proveedor global de datos', async () => {
    signInAsAdmin();
    window.history.pushState({}, '', '/exercises');

    renderWithProviders(<App />);

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Ejercicios' }, { timeout: 3000 }),
    ).toBeInTheDocument();
  });
});
