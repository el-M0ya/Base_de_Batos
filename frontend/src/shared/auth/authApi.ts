/**
 * Authentication API layer: contract, real implementation and selection.
 *
 * @remarks
 * Every authentication call goes through this abstraction, so the rest of the
 * application depends on neither the mock nor the real implementation.
 * The active implementation is chosen from `VITE_API_MODE` (E4-05).
 */
import { ApiError } from '../api/apiError';
import { httpClient } from '../api/httpClient';
import { messages } from '../i18n/messages';
import type { AuthenticatedUser, UserRole } from '../types/roles';
import { authApiMock } from './authApi.mock';

/** Result of a successful login: the access token and its user. */
export interface AuthSession {
  /** Access token sent as `Authorization: Bearer <token>`. */
  token: string;
  /** Authenticated user, with role and capabilities. */
  user: AuthenticatedUser;
}

/**
 * Authentication API contract.
 */
export interface AuthApi {
  /**
   * Logs in with email and password.
   * @throws {@link ApiError} with `status = 401` when the credentials are
   * invalid or the account is inactive (see {@link isInactiveAccountError}).
   */
  login(email: string, password: string): Promise<AuthSession>;

  /** Ends the current user's session. */
  logout(): Promise<void>;

  /**
   * Checks a token and returns its user with up-to-date data.
   * Returns `null` when the token is no longer valid.
   * @throws {@link ApiError} on network or server errors.
   */
  me(token: string): Promise<AuthenticatedUser | null>;
}

/** User as sent by the backend in `/auth/login` and `/auth/me`. */
interface RawUser {
  id: number;
  email: string;
  role: string;
  capabilities: { can_generate: boolean; can_validate: boolean };
}

/** Backend response for `POST /auth/login`. */
interface RawLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: RawUser;
}

/** Persisted roles the frontend knows how to represent. */
const KNOWN_ROLES: readonly UserRole[] = ['administrator', 'trainer', 'client'];

/**
 * Maps the backend user to the frontend shape.
 * @throws {@link ApiError} when the backend sends an unknown role.
 */
function toAuthenticatedUser(raw: RawUser): AuthenticatedUser {
  if (!KNOWN_ROLES.includes(raw.role as UserRole)) {
    throw new ApiError(500, messages.login.sessionError);
  }
  return {
    id: String(raw.id),
    email: raw.email,
    role: raw.role as UserRole,
    capabilities: { ...raw.capabilities },
  };
}

/**
 * Real implementation against the backend (E4-01, `/api/v1/auth`).
 */
export const authApiReal: AuthApi = {
  /** Sends the credentials to `POST /auth/login` and returns token and user. */
  async login(email: string, password: string): Promise<AuthSession> {
    const response = await httpClient.post<RawLoginResponse>('/auth/login', { email, password });
    return { token: response.access_token, user: toAuthenticatedUser(response.user) };
  },

  /** Ends the session; it does not call the backend, which has no logout endpoint. */
  async logout(): Promise<void> {
    // The token expires on its own; forgetting it in the browser is enough.
  },

  /** Checks the token with `GET /auth/me`; returns `null` when the backend rejects it. */
  async me(token: string): Promise<AuthenticatedUser | null> {
    try {
      const raw = await httpClient.get<RawUser>('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      return toAuthenticatedUser(raw);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) return null;
      throw error;
    }
  },
};

/**
 * Tells whether a login error was caused by an inactive account.
 *
 * @remarks
 * The backend answers 401 both for wrong credentials and for inactive
 * accounts; only the text (`"The account is inactive."`) tells them apart. If
 * the backend adds a `code` (e.g. `ACCOUNT_INACTIVE`), only this function needs
 * to change.
 */
export function isInactiveAccountError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401 && /inactive/i.test(error.message);
}

/**
 * Active API mode: 'mock' (default) or 'real'.
 * Read from `VITE_API_MODE`; any other value is treated as mock.
 */
const API_MODE: 'mock' | 'real' = import.meta.env.VITE_API_MODE === 'real' ? 'real' : 'mock';

/**
 * Active authentication implementation.
 */
export const authApi: AuthApi = API_MODE === 'real' ? authApiReal : authApiMock;
