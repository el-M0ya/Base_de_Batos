/**
 * Pruebas de navegación y enrutado (`src/app/router.tsx`).
 *
 * @remarks
 * Comprueba que `RouteGuard` bloquea el contenido cuando no hay sesión
 * autenticada y que los componentes de las rutas del shell se renderizan
 * correctamente. Los clics en enlaces (`<a>`) no se prueban aquí porque jsdom
 * no implementa la navegación a otro documento.
 */
import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { render, cleanup, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../shared/auth/AuthContext';
import { DashboardView } from './DashboardView';
import { ComingSoonView } from './ComingSoonView';
import { NotFoundView } from './NotFoundView';
import { RouteGuard } from './RouteGuard';
import type { UserRole, UserCapabilities } from '../shared/types/roles';

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
});

function renderRoute(element: React.ReactNode, roles?: string[], capabilities?: string[]) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route
            path="*"
            element={
              <RouteGuard
                roles={roles as unknown as UserRole[]}
                capabilities={capabilities as unknown as (keyof UserCapabilities)[]}
                element={element}
              />
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe('Router - RouteGuard protege las rutas', () => {
  it('no muestra el contenido sin sesión autenticada', () => {
    renderRoute(<DashboardView />);

    expect(screen.queryByText(/Bienvenido/)).not.toBeInTheDocument();
  });
});

describe('Componentes de ruta', () => {
  it('muestra el dashboard', () => {
    render(<DashboardView />);

    expect(screen.getByText(/Bienvenido al sistema de generación automática/)).toBeInTheDocument();
  });

  it('muestra ComingSoonView con la sección indicada', () => {
    render(<ComingSoonView section="Ejercicios" />);

    expect(screen.getByText('Próximamente: Ejercicios')).toBeInTheDocument();
  });
});

describe('NotFoundView', () => {
  it('muestra la página de no encontrado', () => {
    render(<NotFoundView />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Página no encontrada' }),
    ).toBeInTheDocument();
    expect(screen.getByText('La ruta solicitada no existe.')).toBeInTheDocument();
  });
});
