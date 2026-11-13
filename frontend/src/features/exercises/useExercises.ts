import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';
import { getExerciseApi } from './exerciseApiSelector';
import type { Exercise, ExerciseCatalogs, ExerciseClassificationInput } from './types';

/** Cache key for the exercise list. */
export const exercisesQueryKey = ['exercises'] as const;

/** Cache key for the exercise classification catalogs. */
export const exerciseCatalogsQueryKey = ['exercise-catalogs'] as const;

/**
 * Loads the exercise catalog.
 *
 * @returns TanStack Query state for the exercises.
 */
export function useExercises(): UseQueryResult<Exercise[], Error> {
  return useQuery({
    queryKey: exercisesQueryKey,
    queryFn: () => getExerciseApi().list(),
  });
}

/**
 * Loads the catalogs required by the exercise classification form.
 *
 * @returns TanStack Query state for the exercise catalogs.
 */
export function useExerciseCatalogs(): UseQueryResult<ExerciseCatalogs, Error> {
  return useQuery({
    queryKey: exerciseCatalogsQueryKey,
    queryFn: () => getExerciseApi().getCatalogs(),
  });
}

/**
 * Updates an exercise classification and refreshes the exercise list.
 *
 * @returns Mutation state for the classification update.
 */
export function useUpdateExerciseClassification(): UseMutationResult<
  Exercise,
  Error,
  { id: string; input: ExerciseClassificationInput }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => getExerciseApi().updateClassification(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: exercisesQueryKey }),
  });
}
