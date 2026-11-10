import { ApiError } from './apiError';
import type { MuscleGroup, MuscleGroupApi, MuscleGroupInput } from '../types/muscleGroup';

/** Demo records used when no backend is available. */
let records: MuscleGroup[] = [
  {
    id: 'muscle-group-1',
    name: 'Pecho',
    description: 'Músculos pectorales.',
    createdAt: '2026-01-01T00:00:00.000Z',
  },
  {
    id: 'muscle-group-2',
    name: 'Espalda',
    description: 'Músculos dorsales y de la espalda alta.',
    createdAt: '2026-01-02T00:00:00.000Z',
  },
];

/** Resolves a copied value asynchronously to mimic a network request. */
function resolve<T>(value: T): Promise<T> {
  return Promise.resolve(structuredClone(value));
}

/** Normalizes names for case-insensitive duplicate checks. */
function normalizeName(name: string): string {
  return name.trim().toLocaleLowerCase();
}

/** Throws the same shape of error that the backend uses for invalid input. */
function ensureUniqueName(name: string, ignoredId?: string): void {
  const duplicate = records.some(
    (record) => record.id !== ignoredId && normalizeName(record.name) === normalizeName(name),
  );
  if (duplicate) {
    throw new ApiError(409, 'Ya existe un grupo muscular con ese nombre.', 'DUPLICATE_NAME');
  }
}

/** In-memory implementation used for local development and tests. */
export const muscleGroupApiMock: MuscleGroupApi = {
  /** Returns a copy of the demo catalog. */
  list(): Promise<MuscleGroup[]> {
    return resolve(records);
  },

  /** Adds a record after validating its unique name. */
  async create(input: MuscleGroupInput): Promise<MuscleGroup> {
    ensureUniqueName(input.name);
    const now = new Date().toISOString();
    const record: MuscleGroup = {
      id: `muscle-group-${Date.now()}`,
      name: input.name.trim(),
      description: input.description.trim(),
      createdAt: now,
      updatedAt: now,
    };
    records = [...records, record];
    return resolve(record);
  },

  /** Updates a record after validating its unique name. */
  async update(id: string, input: MuscleGroupInput): Promise<MuscleGroup> {
    ensureUniqueName(input.name, id);
    const current = records.find((record) => record.id === id);
    if (current === undefined) throw new ApiError(404, 'El grupo muscular no existe.');

    const updated: MuscleGroup = {
      ...current,
      name: input.name.trim(),
      description: input.description.trim(),
      updatedAt: new Date().toISOString(),
    };
    records = records.map((record) => (record.id === id ? updated : record));
    return resolve(updated);
  },

  /** Removes a record from the in-memory catalog. */
  async remove(id: string): Promise<undefined> {
    if (!records.some((record) => record.id === id)) {
      throw new ApiError(404, 'El grupo muscular no existe.');
    }
    records = records.filter((record) => record.id !== id);
    return undefined;
  },
};
