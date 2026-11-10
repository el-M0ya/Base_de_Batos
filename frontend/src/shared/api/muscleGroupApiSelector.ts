import { muscleGroupApi } from './muscleGroupApi';
import { muscleGroupApiMock } from './muscleGroupApi.mock';
import type { MuscleGroupApi } from '../types/muscleGroup';

/**
 * Selects the real or in-memory implementation.
 *
 * @returns The API implementation configured for the current environment.
 */
export function getMuscleGroupApi(): MuscleGroupApi {
  return import.meta.env.VITE_API_MODE === 'real' ? muscleGroupApi : muscleGroupApiMock;
}
