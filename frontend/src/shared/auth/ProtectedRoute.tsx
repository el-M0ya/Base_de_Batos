/**
 * Guarda de ruta basada en rol y capacidad.
 *
 * @remarks
 * Redirige a los usuarios no autenticados al login y bloquea el acceso a las
 * rutas que requieren un rol o capacidad específicos. Las guardas son ayuda de
 * usabilidad, no seguridad: el backend autoriza en cada endpoint.
 *
 * La redirección se hace con `window.location` dentro de un `useEffect`, por
 * lo que el componente funciona tanto dentro como fuera de un `Router` de
 * React Router (por ejemplo, en pruebas de unidad aisladas). Cuando el
 * enrutador de la aplicación está activo, la recarga restaurará la sesión desde
 * `sessionStorage` y volverá a montar el router.
 */
import { useEffect } from 'react';
import type { UserRole } from '../types/roles';
import type { UserCapabilities } from '../types/roles';
import { useAuth } from './useAuth';

/**
 * Props de `ProtectedRoute`.
 */
export interface ProtectedRouteProps {
  /** Contenido que se renderiza si el usuario está autorizado. */
  children: React.ReactNode;
  /** Rol requerido para acceder (opcional). */
  requiredRole?: UserRole;
  /** Capacidad requerida para acceder (opcional). */
  requiredCapability?: keyof UserCapabilities;
  /** Ruta a la que redirigir si no está autenticado. Por defecto `/login`. */
  loginPath?: string;
  /** Ruta a la que redirigir si está autenticado pero no autorizado. Opcional. */
  unauthorizedPath?: string;
}

/**
 * Componente guarda de ruta.
 *
 * @remarks
 * Si el usuario no está autenticado, redirige al login.
 * Si está autenticado pero no cumple el rol o la capacidad requeridos,
 * redirige a `unauthorizedPath` (si se indica) o renderiza `null`.
 * Durante la carga de la sesión, no renderiza nada.
 * El `useEffect` se llama siempre de forma incondicional, respetando las
 * reglas de los hooks de React.
 */
export function ProtectedRoute({
  children,
  requiredRole,
  requiredCapability,
  loginPath = '/login',
  unauthorizedPath,
}: ProtectedRouteProps): React.ReactNode {
  const { user, isAuthenticated, isLoading, hasRole, hasCapability } = useAuth();
  // Determinar si el usuario está autorizado y a dónde redirigir si no lo está.
  let isAuthorized = false;
  let redirectTo: string | null = null;

  if (!isAuthenticated || !user) {
    // No autenticado: redirigir al login.
    redirectTo = loginPath;
  } else if (requiredRole !== undefined && !hasRole(requiredRole)) {
    // Autenticado pero sin el rol requerido: bloquear y redirigir si se indica.
    redirectTo = unauthorizedPath ?? null;
  } else if (requiredCapability !== undefined && !hasCapability(requiredCapability)) {
    // Autenticado pero sin la capacidad requerida: bloquear y redirigir si se indica.
    redirectTo = unauthorizedPath ?? null;
  } else {
    // Autenticado y cumple los requisitos: autorizado.
    isAuthorized = true;
  }

  // Ejecutar la redirección como efecto secundario (no durante el render).
  // Se llama siempre, incluso si redirectTo es null, para respetar las reglas de hooks.
  // Ejecutar la redirección como efecto secundario (no durante el render).
  // Se llama siempre, incluso si redirectTo es null, para respetar las reglas de hooks.
  useEffect(() => {
    if (redirectTo) {
      try {
        window.location.href = redirectTo;
      } catch {
        // En entornos de prueba (jsdom) cambiar location.href no está permitido;
        // la protección se sigue aplicando al no renderizar los hijos.
      }
    }
  }, [redirectTo]);

  // Si todavía se está cargando la sesión o el usuario no está autorizado, no renderizar hijos.
  if (isLoading || !isAuthorized) {
    return null;
  }

  // Autorizado: renderizar los hijos.
  return children;
}

export default ProtectedRoute;
