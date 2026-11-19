import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';
import { getTrainingProgramApi } from './trainingProgramApiSelector';
import type { TrainingProgram, TrainingProgramInput } from './types';

/** Stable cache key for training programs. */
export const trainingProgramsQueryKey = ['training-programs'] as const;

/**
 * Loads all training programs.
 *
 * @returns TanStack Query state for the program catalog.
 */
export function useTrainingPrograms(): UseQueryResult<TrainingProgram[], Error> {
  return useQuery({
    queryKey: trainingProgramsQueryKey,
    queryFn: () => getTrainingProgramApi().list(),
  });
}

/**
 * Creates a program and invalidates the catalog cache.
 *
 * @returns Mutation state for the create operation.
 */
export function useCreateTrainingProgram(): UseMutationResult<
  TrainingProgram,
  Error,
  TrainingProgramInput
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input) => getTrainingProgramApi().create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: trainingProgramsQueryKey }),
  });
}

/**
 * Updates a program and invalidates the catalog cache.
 *
 * @returns Mutation state for the update operation.
 */
export function useUpdateTrainingProgram(): UseMutationResult<
  TrainingProgram,
  Error,
  { id: string; input: TrainingProgramInput }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }) => getTrainingProgramApi().update(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: trainingProgramsQueryKey }),
  });
}

/**
 * Deletes a program and invalidates the catalog cache.
 *
 * @returns Mutation state for the delete operation.
 */
export function useDeleteTrainingProgram(): UseMutationResult<undefined, Error, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => getTrainingProgramApi().remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: trainingProgramsQueryKey }),
  });
}
