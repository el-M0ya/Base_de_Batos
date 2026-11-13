import type { MuscleGroup } from '../../shared/types/muscleGroup';

/** Exercise record exposed by the frontend exercise catalog. */
export interface Exercise {
  /** Unique exercise identifier. */
  id: string;
  /** Exercise name. */
  name: string;
  /** Optional exercise description. */
  description?: string;
  /** Registration date supplied by the backend. */
  registrationDate?: string;
  /** Catalog value describing the exercise type. */
  exerciseType: string;
  /** Catalog value describing the exercise intensity. */
  intensity: string;
  /** Muscle-group identifier. */
  muscleGroupId: string;
  /** Display name of the associated muscle group. */
  muscleGroupName: string;
  /** Identifier of the user who created the exercise. */
  trainerId: string;
}

/** Classification values accepted by the update operation. */
export interface ExerciseClassificationInput {
  /** Selected muscle-group identifier. */
  muscleGroupId: string;
  /** Selected exercise-type catalog value. */
  exerciseType: string;
  /** Selected intensity catalog value. */
  intensity: string;
}

/** Catalog options required by the exercise classification form. */
export interface ExerciseCatalogs {
  /** Available muscle groups. */
  muscleGroups: MuscleGroup[];
  /** Available exercise-type values. */
  exerciseTypes: string[];
  /** Available intensity values. */
  intensityLevels: string[];
}

/** Data contract implemented by the real and mock exercise APIs. */
export interface ExerciseApi {
  /** Retrieves the exercise catalog. */
  list(): Promise<Exercise[]>;
  /** Retrieves classification options for the exercise form. */
  getCatalogs(): Promise<ExerciseCatalogs>;
  /** Updates an exercise classification. */
  updateClassification(id: string, input: ExerciseClassificationInput): Promise<Exercise>;
}
