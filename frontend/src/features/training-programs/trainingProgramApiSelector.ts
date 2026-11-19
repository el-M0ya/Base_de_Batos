import { trainingProgramApi } from './trainingProgramApi';
import { trainingProgramApiMock } from './trainingProgramApi.mock';
import type { TrainingProgramApi } from './types';

/**
 * Selects the real or in-memory program API.
 *
 * @returns The implementation configured through `VITE_API_MODE`.
 */
export function getTrainingProgramApi(): TrainingProgramApi {
  return import.meta.env.VITE_API_MODE === 'real' ? trainingProgramApi : trainingProgramApiMock;
}
