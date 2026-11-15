/**
 * Authentication session context.
 *
 * @remarks
 * Keeps the authenticated user, their role and capabilities in memory.
 * The token is stored both in memory and in `sessionStorage` (see
 * `sessionStore`) so a page reload restores the session in the same tab. On
 * restore, the user is fetched again from the backend (`authApi.me`) to get
 * their current role and capabilities.
 *
 * The provider tells `httpClient` how to get the token and what to do on a 401,
 * so every request carries the session (E4-05).
 *
 * This context lives in `shared/auth` because the layout and several features
 * need it, following the E3-02 dependency rules.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { httpClient } from '../api/httpClient';
import type { AuthenticatedUser, UserCapabilities, UserRole } from '../types/roles';
import { authApi } from './authApi';
import { sessionStore } from './sessionStore';

/**
 * Value of the authentication context.
 */
export interface AuthContextValue {
  /** Authenticated user, or `null` when there is no session. */
  user: AuthenticatedUser | null;
  /** Session token in memory, or `null` when there is no session. */
  token: string | null;
  /** `true` when a user is authenticated. */
  isAuthenticated: boolean;
  /**
   * `true` only while the stored session is being validated at startup.
   *
   * @remarks
   * It does not change during `login`/`logout`: the router hides the whole app
   * while it is `true`, and doing so on login would unmount the login page
   * (losing its error message). Each form keeps its own submitting state.
   */
  isLoading: boolean;
  /**
   * Logs in with email and password.
   * Stores the token in memory and in `sessionStorage`.
   */
  login: (email: string, password: string) => Promise<void>;
  /** Logs out: clears memory and `sessionStorage`. */
  logout: () => Promise<void>;
  /**
   * Restores the stored session (e.g. after a reload), validating the token
   * with the backend.
   */
  restoreSession: () => Promise<void>;
  /** Checks whether the user has the given role. */
  hasRole: (role: UserRole) => boolean;
  /** Checks whether the user has the given capability. */
  hasCapability: (capability: keyof UserCapabilities) => boolean;
}

/** React context for the authentication session. */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Session provider. It must wrap the application (or at least the parts that
 * need authentication).
 *
 * @param children - Child components that consume `useAuth`.
 */
export function AuthProvider({ children }: { children: ReactNode }): React.ReactNode {
  const [token, setToken] = useState<string | null>(() => sessionStore.readToken());
  // Without a token there is no session to restore: no user and nothing to wait for.
  const [user, setUser] = useState<AuthenticatedUser | null>(() =>
    token !== null ? sessionStore.readUser() : null,
  );
  const [isLoading, setIsLoading] = useState(token !== null);

  // Copy of the token that updates immediately (without waiting for a new
  // render), so httpClient never sends a stale token.
  const tokenRef = useRef<string | null>(token);

  const isAuthenticated = user !== null;

  /** Stores the token and user in memory and in `sessionStorage`. */
  const persistSession = useCallback((authToken: string, authUser: AuthenticatedUser) => {
    tokenRef.current = authToken;
    setToken(authToken);
    setUser(authUser);
    sessionStore.save(authToken, authUser);
  }, []);

  /** Clears the session from memory and `sessionStorage`. */
  const clearSession = useCallback(() => {
    tokenRef.current = null;
    setToken(null);
    setUser(null);
    sessionStore.clear();
  }, []);

  // Plug the session into the HTTP client: token on every request, logout on 401.
  useEffect(() => {
    httpClient.setAuthHandlers({
      getToken: () => tokenRef.current,
      onUnauthorized: () => {
        sessionStore.markExpired();
        clearSession();
      },
    });
    return () => httpClient.setAuthHandlers(null);
  }, [clearSession]);

  /** Logs in with email and password. */
  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const session = await authApi.login(email, password);
      persistSession(session.token, session.user);
    },
    [persistSession],
  );

  /** Logs out. */
  const logout = useCallback(async (): Promise<void> => {
    try {
      await authApi.logout();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  /** Restores the stored session, asking the backend for the current user. */
  const restoreSession = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      const storedToken = sessionStore.readToken();
      if (!storedToken) {
        clearSession();
        return;
      }
      const freshUser = await authApi.me(storedToken);
      if (freshUser) {
        persistSession(storedToken, freshUser);
      } else {
        clearSession();
      }
    } catch {
      // The token cannot be verified (like backend down), so ask for a new login.
      clearSession();
    } finally {
      setIsLoading(false);
    }
  }, [clearSession, persistSession]);

  // Validate the stored session once, when the provider mounts. It is scheduled
  // as an async task so state is not updated synchronously inside the effect.
  useEffect(() => {
    if (sessionStore.readToken() === null) return;
    void Promise.resolve().then(restoreSession);
  }, [restoreSession]);

  /** Checks whether the user has the given role. */
  const hasRole = useCallback((role: UserRole): boolean => user?.role === role, [user]);

  /** Checks whether the user has the given capability. */
  const hasCapability = useCallback(
    (capability: keyof UserCapabilities): boolean => user?.capabilities[capability] === true,
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
    [
      user,
      token,
      isAuthenticated,
      isLoading,
      login,
      logout,
      restoreSession,
      hasRole,
      hasCapability,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to consume the authentication context.
 *
 * @returns The authentication context value.
 * @throws {Error} when used outside an `AuthProvider`.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider.');
  }
  return context;
}
