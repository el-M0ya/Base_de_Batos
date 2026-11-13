import { ApiError } from '../../shared/api/apiError';
import type { Exercise, ExerciseApi, ExerciseCatalogs, ExerciseClassificationInput } from './types';

const catalogs: ExerciseCatalogs = {
  muscleGroups: [
    { id: '1', name: 'Pecho', description: '' },
    { id: '2', name: 'Espalda', description: '' },
    { id: '3', name: 'Piernas', description: '' },
  ],
  exerciseTypes: ['fuerza', 'cardio', 'flexibilidad'],
  intensityLevels: ['bajo', 'medio', 'alto'],
};

let records: Exercise[] = [
  {
    id: 'exercise-1',
    name: 'Press de banca',
    description: 'Trabajo de fuerza para el pecho.',
    registrationDate: '2026-01-10',
    exerciseType: 'fuerza',
    intensity: 'alto',
    muscleGroupId: '1',
    muscleGroupName: 'Pecho',
    trainerId: 'trainer-1',
  },
  {
    id: 'exercise-2',
    name: 'Remo con barra',
    description: 'Trabajo de fuerza para la espalda.',
    registrationDate: '2026-01-11',
    exerciseType: 'fuerza',
    intensity: 'medio',
    muscleGroupId: '2',
    muscleGroupName: 'Espalda',
    trainerId: 'trainer-2',
  },
  {
    id: 'exercise-3',
    name: 'Caminata ligera',
    description: 'Actividad cardiovascular de baja intensidad.',
    registrationDate: '2026-01-12',
    exerciseType: 'cardio',
    intensity: 'bajo',
    muscleGroupId: '3',
    muscleGroupName: 'Piernas',
    trainerId: 'client-1',
  },
];

function clone<T>(value: T): T {
  return structuredClone(value);
}

function validateInput(input: ExerciseClassificationInput): void {
  if (
    input.muscleGroupId.trim() === '' ||
    input.exerciseType.trim() === '' ||
    input.intensity.trim() === ''
  ) {
    throw new ApiError(422, 'La clasificación del ejercicio es obligatoria.', 'INVALID_INPUT');
  }
  if (!catalogs.muscleGroups.some((group) => group.id === input.muscleGroupId)) {
    throw new ApiError(422, 'El grupo muscular no es válido.', 'INVALID_MUSCLE_GROUP');
  }
  if (!catalogs.exerciseTypes.includes(input.exerciseType)) {
    throw new ApiError(422, 'El tipo de ejercicio no es válido.', 'INVALID_EXERCISE_TYPE');
  }
  if (!catalogs.intensityLevels.includes(input.intensity)) {
    throw new ApiError(422, 'La intensidad no es válida.', 'INVALID_INTENSITY');
  }
}

function ensureNoDuplicate(record: Exercise, input: ExerciseClassificationInput): void {
  const duplicate = records.some(
    (candidate) =>
      candidate.id !== record.id &&
      candidate.name.trim().toLocaleLowerCase() === record.name.trim().toLocaleLowerCase() &&
      candidate.muscleGroupId === input.muscleGroupId,
  );
  if (duplicate) {
    throw new ApiError(
      409,
      'Ya existe un ejercicio con ese nombre en el grupo muscular seleccionado.',
      'DUPLICATE_EXERCISE',
    );
  }
}

/** In-memory exercise API used until the real E5-01 contract is available. */
export const exerciseApiMock: ExerciseApi = {
  /** Returns a copy of the demo exercise catalog. */
  async list(): Promise<Exercise[]> {
    return clone(records);
  },

  /** Returns a copy of the demo classification catalogs. */
  async getCatalogs(): Promise<ExerciseCatalogs> {
    return clone(catalogs);
  },

  /** Updates a demo classification with the same validation errors as the API. */
  async updateClassification(id: string, input: ExerciseClassificationInput): Promise<Exercise> {
    validateInput(input);
    const current = records.find((record) => record.id === id);
    if (current === undefined) {
      throw new ApiError(404, 'El ejercicio no existe.', 'EXERCISE_NOT_FOUND');
    }
    ensureNoDuplicate(current, input);

    const group = catalogs.muscleGroups.find((item) => item.id === input.muscleGroupId);
    const updated: Exercise = {
      ...current,
      muscleGroupId: input.muscleGroupId,
      muscleGroupName: group?.name ?? '',
      exerciseType: input.exerciseType,
      intensity: input.intensity,
    };
    records = records.map((record) => (record.id === id ? updated : record));
    return clone(updated);
  },
};
