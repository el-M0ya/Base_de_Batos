/**
 * Simulated implementation of the authentication API.
 *
 * @remarks
 * Provides four active demo users: administrator, trainer, room chief
 * (trainer with `can_validate = true`) and client, plus one inactive account
 * to show that error.
 * It simulates network delay and answers with the same errors as the real
 * backend (E4-01), so the demo and the tests reflect the real behaviour.
 * The credentials are fictitious and never reuse real data.
 */
import { ApiError } from '../api/apiError';
import type { AuthenticatedUser, UserCapabilities, UserRole } from '../types/roles';
import type { AuthApi, AuthSession } from './authApi';

/**
 * Demo user used by the simulated API.
 */
export interface DemoUser {
  /** Email of the demo user. */
  email: string;
  /** Password of the demo user (fictitious). */
  password: string;
  /** Persisted role of the user. */
  role: UserRole;
  /** Active capabilities of the user. */
  capabilities: UserCapabilities;
  /** `false` when the account is deactivated (soft delete). */
  active: boolean;
}

const DEMO_USERS: DemoUser[] = [
  {
    email: 'admin@forjafit.demo',
    password: 'admin2026',
    role: 'administrator',
    capabilities: { can_generate: false, can_validate: false },
    active: true,
  },
  {
    email: 'trainer@forjafit.demo',
    password: 'trainer2026',
    role: 'trainer',
    capabilities: { can_generate: true, can_validate: false },
    active: true,
  },
  {
    email: 'chief@forjafit.demo',
    password: 'chief2026',
    role: 'trainer',
    capabilities: { can_generate: true, can_validate: true },
    active: true,
  },
  {
    email: 'client@forjafit.demo',
    password: 'client2026',
    role: 'client',
    capabilities: { can_generate: false, can_validate: false },
    active: true,
  },
  {
    email: 'inactive@forjafit.demo',
    password: 'inactive2026',
    role: 'client',
    capabilities: { can_generate: false, can_validate: false },
    active: false,
  },
];

/** Prefix of the simulated tokens: `demo:<email>`. */
const DEMO_TOKEN_PREFIX = 'demo:';

/** Simulated network delay, in milliseconds. */
const SIMULATED_DELAY_MS = 400;

/**
 * Finds a demo user by email and password.
 * Returns `null` when the credentials do not match.
 */
function findUser(email: string, password: string): DemoUser | null {
  return DEMO_USERS.find((u) => u.email === email.toLowerCase() && u.password === password) ?? null;
}

/**
 * Converts a demo user into an `AuthenticatedUser` with a stable identifier.
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
 * Simulates an authentication API call with network delay.
 */
async function withDelay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), SIMULATED_DELAY_MS);
  });
}

/**
 * Simulated authentication API.
 */
export const authApiMock: AuthApi = {
  /**
   * Logs in with email and password.
   * Rejects with a 401 `ApiError`, using the backend's wording, when the
   * credentials are invalid or the account is inactive.
   */
  async login(email: string, password: string): Promise<AuthSession> {
    await withDelay(undefined);
    const user = findUser(email, password);
    if (!user) {
      throw new ApiError(401, 'Invalid email or password.');
    }
    if (!user.active) {
      throw new ApiError(401, 'The account is inactive.');
    }
    return { token: `${DEMO_TOKEN_PREFIX}${user.email}`, user: toAuthenticatedUser(user) };
  },

  /** Ends the simulated session (there is no server state to clear). */
  async logout(): Promise<void> {
    await withDelay(undefined);
  },

  /** Returns the user of a simulated token, or `null` when it is not valid. */
  async me(token: string): Promise<AuthenticatedUser | null> {
    await withDelay(undefined);
    if (!token.startsWith(DEMO_TOKEN_PREFIX)) {
      return null;
    }
    const email = token.slice(DEMO_TOKEN_PREFIX.length);
    const user = DEMO_USERS.find((u) => u.email === email && u.active);
    return user ? toAuthenticatedUser(user) : null;
  },
};
