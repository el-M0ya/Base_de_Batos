/**
 * Browser storage of the session (`sessionStorage`).
 *
 * @remarks
 * The only place that knows the keys and format used to store the session.
 * `sessionStorage` survives a tab reload but is cleared when the tab closes.
 * `localStorage` is never used (E3-06).
 */
import type { AuthenticatedUser } from '../types/roles';

const TOKEN_KEY = 'forjafit:token';
const USER_KEY = 'forjafit:user';
const EXPIRED_KEY = 'forjafit:sessionExpired';

/** Read and write operations for the persisted session. */
export const sessionStore = {
  /** Returns the stored token, or `null` when there is none. */
  readToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  },

  /** Returns the stored user, or `null` when there is none or the data is corrupted. */
  readUser(): AuthenticatedUser | null {
    const stored = sessionStorage.getItem(USER_KEY);
    if (stored === null) return null;
    try {
      return JSON.parse(stored) as AuthenticatedUser;
    } catch {
      return null;
    }
  },

  /** Stores the token and user of the active session. */
  save(token: string, user: AuthenticatedUser): void {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  /** Removes the stored token and user. */
  clear(): void {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  },

  /** Records that the session ended because the backend rejected the token. */
  markExpired(): void {
    sessionStorage.setItem(EXPIRED_KEY, '1');
  },

  /** Tells whether the last session ended with a rejected token (does not clear the mark). */
  hasExpired(): boolean {
    return sessionStorage.getItem(EXPIRED_KEY) !== null;
  },

  /**
   * Clears the session-expired mark once the notice has been shown.
   *
   * @remarks
   * Reading and clearing are separate because, in `StrictMode`, React runs some
   * functions twice: if reading cleared the mark, the notice could be lost.
   */
  clearExpired(): void {
    sessionStorage.removeItem(EXPIRED_KEY);
  },
};
