/**
 * Guarda de ruta que admite varios roles y capacidades.
 *
 * @remarks
 * Renderiza `element` solo cuando el usuario está autenticado (delegado a
 * `ProtectedRoute`, que redirige al login si no hay sesión) y cumple al menos
 * uno de los roles o al menos una de las capacidades indicadas. Si se omiten
 * ambos, cualquier usuario autenticado accede.
 *
 * @param element - Contenido que se renderiza si el acceso está autorizado.
 * @param roles - Roles que dan acceso (se satisface con cualquiera).
 * @param capabilities - Capacidades que dan acceso (se satisface con cualquiera).
 */
import type { UserRole } from '../shared/types/roles';
import type { UserCapabilities } from '../shared/types/roles';
import { useAuth } from '../shared/auth/useAuth';
import { ProtectedRoute } from '../shared/auth/ProtectedRoute';

/**
 * Props del guarda de ruta que admite varios roles y capacidades.
 */
export interface RouteGuardProps {
  /** Contenido que se renderiza si el acceso está autorizado. */
  element: React.ReactNode;
  /** Roles que dan acceso (se satisface con cualquiera). */
  roles?: UserRole[] | undefined;
  /** Capacidades que dan acceso (se satisface con cualquiera). */
  capabilities?: (keyof UserCapabilities)[] | undefined;
}

/**
 * Guarda de ruta que admite varios roles y capacidades.
 *
 * @remarks
 * Renderiza `element` solo cuando el usuario está autenticado (delegado a
 * `ProtectedRoute`, que redirige al login si no hay sesión) y cumple al menos
 * uno de los roles o al menos una de las capacidades indicadas. Si se omiten
 * ambos, cualquier usuario autenticado accede.
 *
 * @param props - Propiedades del guarda.
 */
export function RouteGuard({
  element,
  roles,
  capabilities,
}: RouteGuardProps) {
  const { isAuthenticated, hasRole, hasCapability } = useAuth();

  const hasAnyRole =
    !roles || roles.some((role) => hasRole(role));
  const hasAnyCapability =
    !capabilities || capabilities.some((capability) => hasCapability(capability));
  const allowed = isAuthenticated && hasAnyRole && hasAnyCapability;

  return (
    <ProtectedRoute>
      {allowed ? element : null}
    </ProtectedRoute>
  );
}
