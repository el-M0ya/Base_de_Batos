/**
 * Runtime selection between the real HTTP API and the in-browser mock API.
 */

/**
 * Supported API modes.
 */
export type ApiMode = 'real' | 'mock';

/**
 * Reads the configured API mode from the environment.
 *
 * @returns The active API mode.
 */
export function getApiMode(): ApiMode {
  const mode = import.meta.env.VITE_API_MODE;
  return mode === 'mock' ? 'mock' : 'real';
}

/**
 * Whether the application runs against the in-browser mock data.
 *
 * @returns `true` when mock mode is active.
 */
export function isMockMode(): boolean {
  return getApiMode() === 'mock';
}

/**
 * Returns the base URL of the real backend API.
 *
 * @returns The configured base URL.
 */
export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
}