import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';
import { getSiteApi } from './siteApiSelector';
import type { Site, SiteInput } from './types';

/** Stable cache key for the gym-site catalog. */
export const sitesQueryKey = ['sites'] as const;

/**
 * Loads all gym sites.
 *
 * @returns TanStack Query state for the site catalog.
 */
export function useSites(): UseQueryResult<Site[], Error> {
  return useQuery({
    queryKey: sitesQueryKey,
    queryFn: () => getSiteApi().list(),
  });
}

/**
 * Creates a site and invalidates the catalog cache.
 *
 * @returns Mutation state for the create operation.
 */
export function useCreateSite(): UseMutationResult<Site, Error, SiteInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input) => getSiteApi().create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sitesQueryKey }),
  });
}

/**
 * Updates a site and invalidates the catalog cache.
 *
 * @returns Mutation state for the update operation.
 */
export function useUpdateSite(): UseMutationResult<Site, Error, { id: string; input: SiteInput }> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }) => getSiteApi().update(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sitesQueryKey }),
  });
}

/**
 * Deletes a site and invalidates the catalog cache.
 *
 * @returns Mutation state for the delete operation.
 */
export function useDeleteSite(): UseMutationResult<undefined, Error, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => getSiteApi().remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sitesQueryKey }),
  });
}
