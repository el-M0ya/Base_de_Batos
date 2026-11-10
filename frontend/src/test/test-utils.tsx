import { StrictMode, type ReactElement, type ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../shared/auth/AuthContext';

/**
 * Envuelve el componente con los proveedores que necesita una pantalla.
 * Incluye `AuthProvider` (sesión de autenticación, E3-06).
 * A medida que existan, se añaden aquí: caché del servidor (E3-03),
 * sesión (E3-06) y enrutador (E3-05).
 */
function AllProviders({ children }: { children: ReactNode }) {
  return (
    <StrictMode>
      <AuthProvider>{children}</AuthProvider>
    </StrictMode>
  );
}

/**
 * Renderiza con los proveedores comunes y devuelve también un `user`
 * de `user-event` listo para simular interacciones.
 */
export function renderWithProviders(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return {
    user: userEvent.setup(),
    ...render(ui, { wrapper: AllProviders, ...options }),
  };
}

export * from '@testing-library/react';
