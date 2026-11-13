import { httpClient } from '../../shared/api/httpClient';
import type { Exercise, ExerciseApi, ExerciseCatalogs, ExerciseClassificationInput } from './types';

const EXERCISES_ENDPOINT = '/exercises';

interface RawExercise {
  id?: string | number;
  id_exercise?: string | number;
  name: string;
  description?: string | null;
  registrationDate?: string;
  registration_date?: string;
  exerciseType?: string;
  exercise_type?: string;
  intensity: string;
  muscleGroupId?: string | number;
  muscle_group_id?: string | number;
  muscleGroupName?: string;
  muscle_group_name?: string;
  trainerId?: string | number;
  trainer_id?: string | number;
}

interface RawCatalogs {
  muscleGroups?: Array<{
    id?: string | number;
    id_muscle_group?: string | number;
    name: string;
  }>;
  muscle_groups?: Array<{
    id?: string | number;
    id_muscle_group?: string | number;
    name: string;
  }>;
  exerciseTypes?: string[];
  exercise_types?: string[];
  intensityLevels?: string[];
  intensity_levels?: string[];
}

function requireIdentifier(value: string | number | undefined, field: string): string {
  if (value === undefined || value === '') {
    throw new Error(`La respuesta de ejercicios no contiene ${field}.`);
  }
  return String(value);
}

function mapExercise(raw: RawExercise): Exercise {
  return {
    id: requireIdentifier(raw.id ?? raw.id_exercise, 'id'),
    name: raw.name,
    ...(raw.description === undefined || raw.description === null
      ? {}
      : { description: raw.description }),
    ...((raw.registrationDate ?? raw.registration_date)
      ? { registrationDate: raw.registrationDate ?? raw.registration_date }
      : {}),
    exerciseType: raw.exerciseType ?? raw.exercise_type ?? '',
    intensity: raw.intensity,
    muscleGroupId: requireIdentifier(raw.muscleGroupId ?? raw.muscle_group_id, 'muscle_group_id'),
    muscleGroupName: raw.muscleGroupName ?? raw.muscle_group_name ?? '',
    trainerId: requireIdentifier(raw.trainerId ?? raw.trainer_id, 'trainer_id'),
  };
}

function mapCatalogs(raw: RawCatalogs): ExerciseCatalogs {
  const muscleGroups = raw.muscleGroups ?? raw.muscle_groups ?? [];
  return {
    muscleGroups: muscleGroups.map((group) => ({
      id: requireIdentifier(group.id ?? group.id_muscle_group, 'id_muscle_group'),
      name: group.name,
      description: '',
    })),
    exerciseTypes: raw.exerciseTypes ?? raw.exercise_types ?? [],
    intensityLevels: raw.intensityLevels ?? raw.intensity_levels ?? [],
  };
}

/** Real HTTP implementation for the exercise data contract. */
export const exerciseApi: ExerciseApi = {
  /** Retrieves and normalizes exercises from the backend. */
  async list(): Promise<Exercise[]> {
    const records = await httpClient.get<RawExercise[]>(EXERCISES_ENDPOINT);
    return records.map(mapExercise);
  },

  /** Retrieves and normalizes exercise classification catalogs. */
  async getCatalogs(): Promise<ExerciseCatalogs> {
    const catalogs = await httpClient.get<RawCatalogs>(`${EXERCISES_ENDPOINT}/catalogs`);
    return mapCatalogs(catalogs);
  },

  /** Updates a classification and normalizes the returned exercise. */
  async updateClassification(id: string, input: ExerciseClassificationInput): Promise<Exercise> {
    const record = await httpClient.put<RawExercise>(
      `${EXERCISES_ENDPOINT}/${encodeURIComponent(id)}/classification`,
      input,
    );
    return mapExercise(record);
  },
};
