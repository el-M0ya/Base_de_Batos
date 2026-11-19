import { ApiError } from '../../shared/api/apiError';
import type { Site, SiteApi, SiteInput } from './types';

/** Demo sites used when the application runs without a backend. */
let records: Site[] = [
  {
    id: 'site-1',
    name: 'Sede Vedado',
    address: 'Calle 23, Vedado, La Habana',
    registrationDate: '2026-01-01',
  },
  {
    id: 'site-2',
    name: 'Sede Miramar',
    address: 'Avenida 5ta, Miramar, La Habana',
    registrationDate: '2026-01-02',
  },
];

/** Returns a copied value asynchronously to mimic a network request. */
function resolve<T>(value: T): Promise<T> {
  return Promise.resolve(structuredClone(value));
}

/** Normalizes names for case-insensitive uniqueness checks. */
function normalizeName(name: string): string {
  return name.trim().toLocaleLowerCase();
}

/** Ensures that a site name does not conflict with another record. */
function ensureUniqueName(name: string, ignoredId?: string): void {
  const duplicate = records.some(
    (record) => record.id !== ignoredId && normalizeName(record.name) === normalizeName(name),
  );
  if (duplicate) {
    throw new ApiError(409, 'Ya existe una sede con ese nombre.', 'DUPLICATE_NAME');
  }
}

/** In-memory site API used for local development and tests. */
export const siteApiMock: SiteApi = {
  /** Returns a copy of the demo site catalog. */
  list(): Promise<Site[]> {
    return resolve(records);
  },

  /** Creates a site after validating the unique name constraint. */
  async create(input: SiteInput): Promise<Site> {
    ensureUniqueName(input.name);
    const record: Site = {
      id: `site-${Date.now()}`,
      name: input.name.trim(),
      address: input.address.trim(),
      registrationDate: new Date().toISOString().slice(0, 10),
    };
    records = [...records, record];
    return resolve(record);
  },

  /** Updates a site after validating the unique name constraint. */
  async update(id: string, input: SiteInput): Promise<Site> {
    ensureUniqueName(input.name, id);
    const current = records.find((record) => record.id === id);
    if (current === undefined) throw new ApiError(404, 'La sede no existe.');

    const updated: Site = {
      ...current,
      name: input.name.trim(),
      address: input.address.trim(),
      updatedAt: new Date().toISOString(),
    };
    records = records.map((record) => (record.id === id ? updated : record));
    return resolve(updated);
  },

  /** Removes a site from the in-memory catalog. */
  async remove(id: string): Promise<undefined> {
    if (!records.some((record) => record.id === id)) {
      throw new ApiError(404, 'La sede no existe.');
    }
    records = records.filter((record) => record.id !== id);
    return undefined;
  },
};
