/**
 * Pruebas del componente `ProtectedRoute`.
 *
 * @remarks
 * Verifica que los usuarios no autenticados no vean el contenido protegido y
 * que los usuarios con el rol o capacidad requeridos sí puedan acceder. La
 * redirección (`window.location.href`) no se puede comprobar en jsdom, por
 * lo que se valida la ausencia/presencia del contenido.
 */
import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import { AuthProvider } from './AuthContext';
import { ProtectedRoute } from './ProtectedRoute';

function AuthorizedContent() {
  return <div data-testid="authorized-content">Contenido autorizado</div>;
}

function renderRoute(ui: React.ReactNode) {
  return { ...render(<AuthProvider>{ui}</AuthProvider>) };
}

/** Espera a que la validación de sesión asíncrona termine (400 ms del mock). */
async function waitForSession() {
  await new Promise((resolve) => setTimeout(resolve, 600));
}

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
});

/** Guarda una sesión de entrenador en sessionStorage. */
function setTrainerSession() {
  sessionStorage.setItem('forjafit:token', 'demo:trainer@forjafit.demo');
  sessionStorage.setItem(
    'forjafit:user',
    JSON.stringify({
      id: 'user-trainer@forjafit.demo',
      email: 'trainer@forjafit.demo',
      role: 'trainer',
      capabilities: { can_generate: true, can_validate: false },
    }),
  );
}

/** Guarda una sesión de jefe de sala en sessionStorage. */
function setChiefSession() {
  sessionStorage.setItem('forjafit:token', 'demo:chief@forjafit.demo');
  sessionStorage.setItem(
    'forjafit:user',
    JSON.stringify({
      id: 'user-chief@forjafit.demo',
      email: 'chief@forjafit.demo',
      role: 'trainer',
      capabilities: { can_generate: true, can_validate: true },
    }),
  );
}

/** Guarda una sesión de cliente en sessionStorage. */
function setClientSession() {
  sessionStorage.setItem('forjafit:token', 'demo:client@forjafit.demo');
  sessionStorage.setItem(
    'forjafit:user',
    JSON.stringify({
      id: 'user-client@forjafit.demo',
      email: 'client@forjafit.demo',
      role: 'client',
      capabilities: { can_generate: false, can_validate: false },
    }),
  );
}

describe('ProtectedRoute - sin sesión', () => {
  it('no renderiza el contenido cuando no hay sesión', async () => {
    renderRoute(
      <ProtectedRoute requiredRole="trainer">
        <AuthorizedContent />
      </ProtectedRoute>,
    );
    await waitForSession();

    expect(document.querySelector('[data-testid="authorized-content"]')).not.toBeInTheDocument();
  });
});

describe('ProtectedRoute - rol requerido', () => {
  it('permite al entrenador acceder a ruta que requiere rol trainer', async () => {
    setTrainerSession();
    renderRoute(
      <ProtectedRoute requiredRole="trainer">
        <AuthorizedContent />
      </ProtectedRoute>,
    );
    await waitForSession();

    expect(document.querySelector('[data-testid="authorized-content"]')).toBeInTheDocument();
  });

  it('no permite al cliente acceder a ruta que requiere rol trainer', async () => {
    setClientSession();
    renderRoute(
      <ProtectedRoute requiredRole="trainer">
        <AuthorizedContent />
      </ProtectedRoute>,
    );
    await waitForSession();

    expect(document.querySelector('[data-testid="authorized-content"]')).not.toBeInTheDocument();
  });

  it('permite al administrador acceder a ruta que requiere rol administrator', async () => {
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
    renderRoute(
      <ProtectedRoute requiredRole="administrator">
        <AuthorizedContent />
      </ProtectedRoute>,
    );
    await waitForSession();

    expect(document.querySelector('[data-testid="authorized-content"]')).toBeInTheDocument();
  });
});

describe('ProtectedRoute - capacidad requerida', () => {
  it('permite al jefe de sala acceder a ruta que requiere can_validate', async () => {
    setChiefSession();
    renderRoute(
      <ProtectedRoute requiredCapability="can_validate">
        <AuthorizedContent />
      </ProtectedRoute>,
    );
    await waitForSession();

    expect(document.querySelector('[data-testid="authorized-content"]')).toBeInTheDocument();
  });

  it('no permite al entrenador sin can_validate acceder a ruta que requiere can_validate', async () => {
    setTrainerSession();
    renderRoute(
      <ProtectedRoute requiredCapability="can_validate">
        <AuthorizedContent />
      </ProtectedRoute>,
    );
    await waitForSession();

    expect(document.querySelector('[data-testid="authorized-content"]')).not.toBeInTheDocument();
  });

  it('no permite al cliente acceder a ruta que requiere can_generate', async () => {
    setClientSession();
    renderRoute(
      <ProtectedRoute requiredCapability="can_generate">
        <AuthorizedContent />
      </ProtectedRoute>,
    );
    await waitForSession();

    expect(document.querySelector('[data-testid="authorized-content"]')).not.toBeInTheDocument();
  });
});
