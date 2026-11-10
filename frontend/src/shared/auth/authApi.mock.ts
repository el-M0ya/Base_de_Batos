/**
 * Implementación simulada de la API de autenticación.
 *
 * @remarks
 * Proporciona cuatro usuarios de demostración: administrador, entrenador,
 * jefe de sala (entrenador con `can_validate = true`) y cliente.
 * Simula una demora de red para que el comportamiento sea realista.
 * Las credenciales son ficticias y nunca reutilizan datos reales.
 *
 * El backend aún no expone endpoints de autenticación (ver `Agents.md` §13),
 * por lo que el frontend usa esta simulación hasta que existan.
 */
import type { AuthenticatedUser, UserCapabilities, UserRole } from '../types/roles';

/**
 * Usuario de demostración usado por la API simulada.
 */
export interface DemoUser {
  /** Correo electrónico del usuario demo. */
  email: string;
  /** Contraseña del usuario demo (ficticia). */
  password: string;
  /** Rol persistido del usuario. */
  role: UserRole;
  /** Capacidades activas del usuario. */
  capabilities: UserCapabilities;
}

const DEMO_USERS: DemoUser[] = [
  {
    email: 'admin@forjafit.demo',
    password: 'admin2026',
    role: 'administrator',
    capabilities: { can_generate: false, can_validate: false },
  },
  {
    email: 'trainer@forjafit.demo',
    password: 'trainer2026',
    role: 'trainer',
    capabilities: { can_generate: true, can_validate: false },
  },
  {
    email: 'chief@forjafit.demo',
    password: 'chief2026',
    role: 'trainer',
    capabilities: { can_generate: true, can_validate: true },
  },
  {
    email: 'client@forjafit.demo',
    password: 'client2026',
    role: 'client',
    capabilities: { can_generate: false, can_validate: false },
  },
];

/** Demora simulada de red, en milisegundos. */
const SIMULATED_DELAY_MS = 400;

/**
 * Busca un usuario demo por correo y contraseña.
 * Devuelve `null` si las credenciales no coinciden.
 */
function findUser(email: string, password: string): DemoUser | null {
  return (
    DEMO_USERS.find((u) => u.email === email.toLowerCase() && u.password === password) ?? null
  );
}

/**
 * Convierte un usuario demo en un `AuthenticatedUser` con identificador estable.
 */
function toAuthenticatedUser(demo: DemoUser): AuthenticatedUser {
  return {
    id: `user-${demo.email}`,
    email: demo.email,
    role: demo.role,
    capabilities: { ...demo.capabilities },
  };
}

/**
 * Simula una llamada a la API de autenticación con demora de red.
 */
async function withDelay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), SIMULATED_DELAY_MS);
  });
}

/**
 * API de autenticación simulada.
 */
export const authApiMock = {
  /**
   * Inicia sesión con correo y contraseña.
   * Rechaza con un error de estado 401 si las credenciales son inválidas.
   */
  async login(email: string, password: string): Promise<AuthenticatedUser> {
    await withDelay(undefined);
    const user = findUser(email, password);
    if (!user) {
      const error: Error & { status?: number; code?: string } = new Error(
        'Credenciales incorrectas.',
      );
      error.status = 401;
      error.code = 'UNAUTHORIZED';
      throw error;
    }
    return toAuthenticatedUser(user);
  },

  /** Cierra la sesión simulada (no hay estado de servidor que limpiar). */
  async logout(): Promise<void> {
    await withDelay(undefined);
  },

  /** Restaura la sesión desde el token guardado; devuelve `null` si no hay sesión. */
  async me(): Promise<AuthenticatedUser | null> {
    await withDelay(undefined);
    const token = sessionStorage.getItem('forjafit:token');
    if (!token) {
      return null;
    }
    // El token tiene el formato "demo:<email>"; recuperamos el usuario asociado.
    const email = token.replace(/^demo:/, '');
    const user = DEMO_USERS.find((u) => u.email === email);
    if (!user) {
      return null;
    }
    return toAuthenticatedUser(user);
  },
};
