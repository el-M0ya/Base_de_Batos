/**
 * Contexto de sesión de autenticación.
 *
 * @remarks
 * Almacena en memoria el usuario autenticado, su rol y sus capacidades.
 * El token se guarda tanto en memoria como en `sessionStorage` para que una
 * recarga de la página restaure la sesión en la misma pestaña.
 * Nunca se usa `localStorage`.
 *
 * Este contexto vive en `shared/auth` porque el layout y varias features lo
 * necesitan, respetando las reglas de dependencia de E3-02.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { AuthenticatedUser, UserCapabilities, UserRole } from '../types/roles';
import { authApi } from './authApi';

/**
 * Valor del contexto de autenticación.
 */
export interface AuthContextValue {
  /** Usuario autenticado, o `null` si no hay sesión. */
  user: AuthenticatedUser | null;
  /** Token de sesión en memoria, o `null` si no hay sesión. */
  token: string | null;
  /** `true` si hay un usuario autenticado. */
  isAuthenticated: boolean;
  /** `true` mientras se inicia sesión o se valida la sesión almacenada. */
  isLoading: boolean;
  /**
   * Inicia sesión con correo y contraseña.
   * Guarda el token en memoria y en `sessionStorage`.
   */
  login: (email: string, password: string) => Promise<void>;
  /** Cierra la sesión: limpia memoria y `sessionStorage`. */
  logout: () => Promise<void>;
  /**
   * Restaura la sesión desde `sessionStorage` (por ejemplo, tras recargar).
   */
  restoreSession: () => Promise<void>;
  /** Comprueba si el usuario tiene el rol indicado. */
  hasRole: (role: UserRole) => boolean;
  /** Comprueba si el usuario tiene la capacidad indicada. */
  hasCapability: (capability: keyof UserCapabilities) => boolean;
}

/** Contexto de React para la sesión de autenticación. */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Proveedor de sesión. Debe envolver la aplicación (o al menos las partes que
 * necesitan autenticación).
 *
 * @param children - Componentes hijos que consumen `useAuth`.
 */
export function AuthProvider({ children }: { children: ReactNode }): React.ReactNode {
  // Inicializar estado desde sessionStorage (sin setState en efectos).
  const [user, setUser] = useState<AuthenticatedUser | null>(() => {
    const stored = sessionStorage.getItem('forjafit:user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return sessionStorage.getItem('forjafit:token');
  });
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  /** Guarda el token y el usuario en memoria y en `sessionStorage`. */
  const persistSession = useCallback(
    (authToken: string, authUser: AuthenticatedUser) => {
      setToken(authToken);
      setUser(authUser);
      sessionStorage.setItem('forjafit:token', authToken);
      sessionStorage.setItem(
        'forjafit:user',
        JSON.stringify(authUser),
      );
    },
    [],
  );

  /** Limpia la sesión de memoria y de `sessionStorage`. */
  const clearSession = useCallback(() => {
    setToken(null);
    setUser(null);
    sessionStorage.removeItem('forjafit:token');
    sessionStorage.removeItem('forjafit:user');
  }, []);

  /** Inicia sesión con correo y contraseña. */
  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      setIsLoading(true);
      try {
        const authUser = await authApi.login(email, password);
        const authToken = `demo:${authUser.email}`;
        persistSession(authToken, authUser);
      } finally {
        setIsLoading(false);
      }
    },
    [persistSession],
  );

  /** Cierra la sesión. */
  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await authApi.logout();
    } finally {
      clearSession();
      setIsLoading(false);
    }
  }, [clearSession]);

  /** Restaura la sesión desde `sessionStorage`. */
  const restoreSession = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      const storedToken = sessionStorage.getItem('forjafit:token');
      const storedUser = sessionStorage.getItem('forjafit:user');

      if (!storedToken || !storedUser) {
        clearSession();
        return;
      }

      // Verificar con la API que la sesión sigue siendo válida.
      const authUser = await authApi.me();
      if (!authUser) {
        clearSession();
        return;
      }

      const parsedUser: AuthenticatedUser = JSON.parse(storedUser);
      setToken(storedToken);
      setUser(parsedUser);
    } catch {
      clearSession();
    } finally {
      setIsLoading(false);
    }
  }, [clearSession]);

  /** Comprueba si el usuario tiene el rol indicado. */
  const hasRole = useCallback(
    (role: UserRole): boolean => user?.role === role,
    [user],
  );

  /** Comprueba si el usuario tiene la capacidad indicada. */
  const hasCapability = useCallback(
    (capability: keyof UserCapabilities): boolean =>
      user?.capabilities[capability] === true,
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated,
      isLoading,
      login,
      logout,
      restoreSession,
      hasRole,
      hasCapability,
    }),
    [user, token, isAuthenticated, isLoading, login, logout, restoreSession, hasRole, hasCapability],
  );

  // Validar la sesión almacenada con la API tras montar el proveedor.
  // authApi.me() es asíncrona y no llama a setState de forma síncrona.
  useEffect(() => {
    void (async () => {
      if (!token) {
        setIsLoading(false);
        return;
      }
      const authUser = await authApi.me();
      if (!authUser) {
        clearSession();
      }
      setIsLoading(false);
    })();
  }, [token, clearSession]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook para consumir el contexto de autenticación.
 *
 * @returns El valor del contexto de autenticación.
 * @throws {Error} si se usa fuera de un `AuthProvider`.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider.');
  }
  return context;
}
