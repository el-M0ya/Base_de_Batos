/**
 * Capa de API de autenticación: interfaz y selección de implementación.
 *
 * @remarks
 * Todas las llamadas de autenticación pasan por esta abstracción, para que el
 * resto de la aplicación no dependa ni del mock ni de la implementación real.
 * La implementación activa se elige según `VITE_API_MODE`; hasta que existan
 * los endpoints de backend (ver `Agents.md` §13), se usa el mock.
 */
import type { AuthenticatedUser } from '../types/roles';
import { authApiMock } from './authApi.mock';

/**
 * Contrato de la API de autenticación.
 */
export interface AuthApi {
  /**
   * Inicia sesión con correo y contraseña.
   * @throws {Error} con `status = 401` si las credenciales son inválidas.
   */
  login(email: string, password: string): Promise<AuthenticatedUser>;

  /** Cierra la sesión del usuario actual. */
  logout(): Promise<void>;

  /**
   * Restaura la sesión a partir del token persistido.
   * Devuelve `null` si no hay sesión activa.
   */
  me(): Promise<AuthenticatedUser | null>;
}

/**
 * Implementación real (pendiente de endpoints de backend).
 * Mientras tanto, lanza un error claro si se intenta usar.
 */
const authApiReal: AuthApi = {
  async login(): Promise<AuthenticatedUser> {
    throw new Error('Autenticación real no disponible aún: los endpoints de backend no existen.');
  },
  async logout(): Promise<void> {
    throw new Error('Autenticación real no disponible aún: los endpoints de backend no existen.');
  },
  async me(): Promise<AuthenticatedUser | null> {
    throw new Error('Autenticación real no disponible aún: los endpoints de backend no existen.');
  },
};

/**
 * Modo de API activo: 'mock' (por defecto) o 'real'.
 * Se lee de `VITE_API_MODE`; cualquier otro valor se trata como mock.
 */
const API_MODE: 'mock' | 'real' = import.meta.env.VITE_API_MODE === 'real' ? 'real' : 'mock';

/**
 * Implementación de autenticación activa.
 */
export const authApi: AuthApi = API_MODE === 'real' ? authApiReal : authApiMock;
