import { httpClient } from '../../shared/api/httpClient';
import type { TrainingProgram, TrainingProgramApi, TrainingProgramInput } from './types';

/** Endpoint used by the training-program administration API. */
const PROGRAMS_ENDPOINT = '/training-programs';

/**
 * Real HTTP implementation of the training-program API.
 *
 * @remarks
 * The backend is responsible for persisting the `covers` associations as
 * part of the create/update operation.
 */
export const trainingProgramApi: TrainingProgramApi = {
  /** Retrieves programs and their associated muscle groups. */
  list(): Promise<TrainingProgram[]> {
    return httpClient.get<TrainingProgram[]>(PROGRAMS_ENDPOINT);
  },

  /** Creates a program with its selected muscle groups. */
  create(input: TrainingProgramInput): Promise<TrainingProgram> {
    return httpClient.post<TrainingProgram>(PROGRAMS_ENDPOINT, input);
  },

  /** Updates a program and its selected muscle groups. */
  update(id: string, input: TrainingProgramInput): Promise<TrainingProgram> {
    return httpClient.put<TrainingProgram>(`${PROGRAMS_ENDPOINT}/${id}`, input);
  },

  /** Deletes a program and its associations. */
  async remove(id: string): Promise<undefined> {
    await httpClient.delete<undefined>(`${PROGRAMS_ENDPOINT}/${id}`);
    return undefined;
  },
};
