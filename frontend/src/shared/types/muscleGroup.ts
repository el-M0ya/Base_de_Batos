/**
 * Muscle-group catalog record.
 */
export interface MuscleGroup {
  /** Unique identifier assigned by the backend or mock repository. */
  id: string;
  /** Required display name. */
  name: string;
  /** Optional explanation of the muscles covered by the group. */
  description: string;
  /** Creation timestamp when supplied by the backend. */
  createdAt?: string;
  /** Last update timestamp when supplied by the backend. */
  updatedAt?: string;
}

/**
 * Fields accepted by create and update operations.
 */
export interface MuscleGroupInput {
  /** Required display name. */
  name: string;
  /** Optional description. */
  description: string;
}

/** Contract implemented by both real and mock muscle-group APIs. */
export interface MuscleGroupApi {
  /** Retrieves all muscle groups. */
  list(): Promise<MuscleGroup[]>;
  /** Creates a muscle group. */
  create(input: MuscleGroupInput): Promise<MuscleGroup>;
  /** Updates a muscle group. */
  update(id: string, input: MuscleGroupInput): Promise<MuscleGroup>;
  /** Deletes a muscle group. */
  remove(id: string): Promise<undefined>;
}
