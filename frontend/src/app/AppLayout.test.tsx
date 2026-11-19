/**
 * Pruebas del layout de la aplicación (`src/app/AppLayout.tsx`).
 *
 * @remarks
 * Verifica que la barra lateral filtra las entradas de navegación según el
 * rol y las capacidades de la sesión.
 */
import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { render, cleanup, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../shared/auth/AuthContext';
import { AppLayout } from './AppLayout';

function renderLayout(ui: React.ReactNode) {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <Routes>
          <Route path="/" element={ui} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
});

async function waitForSession() {
  await new Promise((resolve) => setTimeout(resolve, 600));
}

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

function setAdminSession() {
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

describe('AppLayout - menú por rol', () => {
  it('entrenador ve Ejercicios, Rutinas e Informes, pero no administración', async () => {
    setTrainerSession();
    renderLayout(<AppLayout />);
    await waitForSession();

    expect(screen.getByText('Ejercicios')).toBeInTheDocument();
    expect(screen.getByText('Rutinas')).toBeInTheDocument();
    expect(screen.getByText('Informes')).toBeInTheDocument();
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument();
    expect(screen.queryByText('Sedes')).not.toBeInTheDocument();
  });

  it('cliente solo ve Inicio e Informes', async () => {
    setClientSession();
    renderLayout(<AppLayout />);
    await waitForSession();

    expect(screen.getByText('Inicio')).toBeInTheDocument();
    expect(screen.getByText('Informes')).toBeInTheDocument();
    expect(screen.queryByText('Ejercicios')).not.toBeInTheDocument();
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument();
  });

  it('administrador ve todas las entradas de administración', async () => {
    setAdminSession();
    renderLayout(<AppLayout />);
    await waitForSession();

    expect(screen.getByText('Usuarios')).toBeInTheDocument();
    expect(screen.getByText('Sedes')).toBeInTheDocument();
    expect(screen.getByText('Programas')).toBeInTheDocument();
    expect(screen.getByText('Grupos musculares')).toBeInTheDocument();
    expect(screen.getByText('Ejercicios')).toBeInTheDocument();
  });
});
