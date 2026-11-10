import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';
import { getMuscleGroupApi } from './muscleGroupApiSelector';
import type { MuscleGroup, MuscleGroupInput } from './types';

/** Stable cache key for the muscle-group catalog. */
export const muscleGroupsQueryKey = ['muscle-groups'] as const;

/**
 * Loads the muscle-group catalog.
 *
 * @returns TanStack Query state for the catalog.
 */
export function useMuscleGroups(): UseQueryResult<MuscleGroup[], Error> {
  return useQuery({
    queryKey: muscleGroupsQueryKey,
    queryFn: () => getMuscleGroupApi().list(),
  });
}

/**
 * Creates a muscle group and refreshes the catalog.
 *
 * @returns Mutation state for the create operation.
 */
export function useCreateMuscleGroup(): UseMutationResult<MuscleGroup, Error, MuscleGroupInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input) => getMuscleGroupApi().create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: muscleGroupsQueryKey }),
  });
}

/**
 * Updates a muscle group and refreshes the catalog.
 *
 * @returns Mutation state for the update operation.
 */
export function useUpdateMuscleGroup(): UseMutationResult<
  MuscleGroup,
  Error,
  { id: string; input: MuscleGroupInput }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }) => getMuscleGroupApi().update(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: muscleGroupsQueryKey }),
  });
}

/**
 * Deletes a muscle group and refreshes the catalog.
 *
 * @returns Mutation state for the delete operation.
 */
export function useDeleteMuscleGroup(): UseMutationResult<undefined, Error, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => getMuscleGroupApi().remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: muscleGroupsQueryKey }),
  });
}
