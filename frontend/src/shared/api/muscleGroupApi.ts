import { httpClient } from './httpClient';
import type { MuscleGroup, MuscleGroupApi, MuscleGroupInput } from '../types/muscleGroup';

/** Endpoint used by the muscle-group catalog. */
const MUSCLE_GROUPS_ENDPOINT = '/muscle-groups';

/**
 * Real HTTP implementation of the muscle-group API.
 *
 * @remarks
 * The feature only consumes the {@link MuscleGroupApi} contract, so changing
 * the endpoint or response mapping remains isolated to this module.
 */
export const muscleGroupApi: MuscleGroupApi = {
  /** Fetches all muscle groups from the backend. */
  list(): Promise<MuscleGroup[]> {
    return httpClient.get<MuscleGroup[]>(MUSCLE_GROUPS_ENDPOINT);
  },

  /** Sends a new muscle group to the backend. */
  create(input: MuscleGroupInput): Promise<MuscleGroup> {
    return httpClient.post<MuscleGroup>(MUSCLE_GROUPS_ENDPOINT, input);
  },

  /** Sends an updated muscle group to the backend. */
  update(id: string, input: MuscleGroupInput): Promise<MuscleGroup> {
    return httpClient.put<MuscleGroup>(`${MUSCLE_GROUPS_ENDPOINT}/${id}`, input);
  },

  /** Deletes a muscle group from the backend. */
  async remove(id: string): Promise<undefined> {
    await httpClient.delete<undefined>(`${MUSCLE_GROUPS_ENDPOINT}/${id}`);
    return undefined;
  },
};
