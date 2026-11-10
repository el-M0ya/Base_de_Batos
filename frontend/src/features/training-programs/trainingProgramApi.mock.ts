import { ApiError } from '../../shared/api/apiError';
import { muscleGroupApiMock } from '../muscle-groups/muscleGroupApi.mock';
import type { TrainingProgram, TrainingProgramApi, TrainingProgramInput } from './types';

/** Demo programs used when the application runs without a backend. */
let records: TrainingProgram[] = [
  {
    id: 'program-1',
    name: 'Fuerza de tren superior',
    objective: 'Mejorar la fuerza de los músculos del tren superior.',
    muscleGroupIds: ['muscle-group-1', 'muscle-group-2'],
    createdAt: '2026-01-03T00:00:00.000Z',
  },
];

/** Resolves a copied value asynchronously to mimic a network request. */
function resolve<T>(value: T): Promise<T> {
  return Promise.resolve(structuredClone(value));
}

/** Normalizes names for case-insensitive uniqueness checks. */
function normalizeName(name: string): string {
  return name.trim().toLocaleLowerCase();
}

/** Ensures that a program name is unique. */
function ensureUniqueName(name: string, ignoredId?: string): void {
  const duplicate = records.some(
    (record) => record.id !== ignoredId && normalizeName(record.name) === normalizeName(name),
  );
  if (duplicate) {
    throw new ApiError(409, 'Ya existe un programa con ese nombre.', 'DUPLICATE_NAME');
  }
}

/** Expands selected identifiers using the same muscle-group API contract. */
async function expandMuscleGroups(program: TrainingProgram): Promise<TrainingProgram> {
  const groups = await muscleGroupApiMock.list();
  return {
    ...program,
    muscleGroups: groups.filter((group) => program.muscleGroupIds.includes(group.id)),
  };
}

/** In-memory training-program API used for local development and tests. */
export const trainingProgramApiMock: TrainingProgramApi = {
  /** Returns programs with expanded muscle-group information. */
  async list(): Promise<TrainingProgram[]> {
    return resolve(await Promise.all(records.map((record) => expandMuscleGroups(record))));
  },

  /** Creates a program after validating its name and group selection. */
  async create(input: TrainingProgramInput): Promise<TrainingProgram> {
    ensureUniqueName(input.name);
    if (input.muscleGroupIds.length === 0) {
      throw new ApiError(422, 'Selecciona al menos un grupo muscular.', 'MUSCLE_GROUPS_REQUIRED');
    }
    const now = new Date().toISOString();
    const record: TrainingProgram = {
      id: `program-${Date.now()}`,
      name: input.name.trim(),
      objective: input.objective.trim(),
      muscleGroupIds: [...input.muscleGroupIds],
      createdAt: now,
      updatedAt: now,
    };
    records = [...records, record];
    return expandMuscleGroups(record);
  },

  /** Updates a program and replaces its muscle-group associations. */
  async update(id: string, input: TrainingProgramInput): Promise<TrainingProgram> {
    ensureUniqueName(input.name, id);
    if (input.muscleGroupIds.length === 0) {
      throw new ApiError(422, 'Selecciona al menos un grupo muscular.', 'MUSCLE_GROUPS_REQUIRED');
    }
    const current = records.find((record) => record.id === id);
    if (current === undefined) throw new ApiError(404, 'El programa no existe.');

    const updated: TrainingProgram = {
      ...current,
      name: input.name.trim(),
      objective: input.objective.trim(),
      muscleGroupIds: [...input.muscleGroupIds],
      updatedAt: new Date().toISOString(),
    };
    records = records.map((record) => (record.id === id ? updated : record));
    return expandMuscleGroups(updated);
  },

  /** Removes a program from the in-memory catalog. */
  async remove(id: string): Promise<undefined> {
    if (!records.some((record) => record.id === id)) {
      throw new ApiError(404, 'El programa no existe.');
    }
    records = records.filter((record) => record.id !== id);
    return undefined;
  },
};
