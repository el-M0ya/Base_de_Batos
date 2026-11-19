import { exerciseApi } from './exerciseApi';
import { exerciseApiMock } from './exerciseApi.mock';
import type { ExerciseApi } from './types';

/**
 * Selects the exercise data source.
 *
 * The mock remains the default until E5-01 exposes and configures the real
 * exercise endpoints. Set `VITE_EXERCISE_API=real` once that contract exists.
 */
export function getExerciseApi(): ExerciseApi {
  const mode = import.meta.env.VITE_EXERCISE_API;
  const baseUrl = import.meta.env.VITE_API_BASE_URL;

  if (mode === 'mock' || (mode !== 'real' && baseUrl === undefined)) {
    return exerciseApiMock;
  }

  return exerciseApi;
}
