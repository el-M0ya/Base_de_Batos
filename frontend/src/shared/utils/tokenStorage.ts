/**
 * Simple in-memory + localStorage token storage used by the HTTP client.
 */

const TOKEN_KEY = 'gym_auth_token';

/**
 * Returns the stored authentication token, if any.
 *
 * @returns The token or `null`.
 */
export function getAuthToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

/**
 * Stores the authentication token.
 *
 * @param token - The token to store.
 */
export function setAuthToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Ignore storage failures (private mode, etc.).
  }
}

/**
 * Removes the stored authentication token.
 */
export function clearAuthToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore storage failures.
  }
}