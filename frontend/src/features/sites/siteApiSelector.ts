import { siteApi } from './siteApi';
import { siteApiMock } from './siteApi.mock';
import type { SiteApi } from './types';

/**
 * Selects the real or in-memory site API for the current environment.
 *
 * @returns The implementation configured through `VITE_API_MODE`.
 */
export function getSiteApi(): SiteApi {
  return import.meta.env.VITE_API_MODE === 'real' ? siteApi : siteApiMock;
}
