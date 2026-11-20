import { httpClient } from '../../shared/api/httpClient';
import type { Site, SiteApi, SiteInput } from './types';

/** Endpoint used by the gym-site administration API. */
const SITES_ENDPOINT = '/sites';

/**
 * Real HTTP implementation of the site API.
 *
 * @remarks
 * Keeping endpoint details in this adapter means views and hooks depend only
 * on the stable {@link SiteApi} contract.
 */
export const siteApi: SiteApi = {
  /** Retrieves the sites from the backend. */
  list(): Promise<Site[]> {
    return httpClient.get<Site[]>(SITES_ENDPOINT);
  },

  /** Creates a site in the backend. */
  create(input: SiteInput): Promise<Site> {
    return httpClient.post<Site>(SITES_ENDPOINT, input);
  },

  /** Updates a site in the backend. */
  update(id: string, input: SiteInput): Promise<Site> {
    return httpClient.put<Site>(`${SITES_ENDPOINT}/${id}`, input);
  },

  /** Removes a site from the backend. */
  async remove(id: string): Promise<undefined> {
    await httpClient.delete<undefined>(`${SITES_ENDPOINT}/${id}`);
    return undefined;
  },
};
