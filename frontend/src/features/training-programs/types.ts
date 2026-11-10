import type { MuscleGroup } from '../muscle-groups/types';

/**
 * Training program record exposed to the frontend.
 *
 * @remarks
 * `muscleGroups` is an expanded representation convenient for rendering,
 * while `muscleGroupIds` is the canonical value sent to the API for the
 * `covers` many-to-many relationship.
 */
export interface TrainingProgram {
  /** Unique identifier assigned by the backend or mock repository. */
  id: string;
  /** Required unique program name. */
  name: string;
  /** Required training objective. */
  objective: string;
  /** Identifiers of muscle groups covered by the program. */
  muscleGroupIds: string[];
  /** Expanded muscle-group records when returned by the API. */
  muscleGroups?: MuscleGroup[];
  /** Creation timestamp when supplied by the backend. */
  createdAt?: string;
  /** Last update timestamp when supplied by the backend. */
  updatedAt?: string;
}

/**
 * Fields accepted by create and update operations.
 */
export interface TrainingProgramInput {
  /** Required unique program name. */
  name: string;
  /** Required objective. */
  objective: string;
  /** Selected muscle-group identifiers. */
  muscleGroupIds: string[];
}

/** Contract shared by real and in-memory training-program APIs. */
export interface TrainingProgramApi {
  /** Retrieves all training programs. */
  list(): Promise<TrainingProgram[]>;
  /** Creates a training program and its muscle-group associations. */
  create(input: TrainingProgramInput): Promise<TrainingProgram>;
  /** Updates a training program and replaces its associations. */
  update(id: string, input: TrainingProgramInput): Promise<TrainingProgram>;
  /** Deletes a training program. */
  remove(id: string): Promise<undefined>;
}
