import { QueryClient } from '@tanstack/react-query';

/**
 * Creates the application-wide TanStack Query client.
 *
 * @returns A configured query client.
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 30_000,
      },
      mutations: {
        retry: 0,
      },
    },
  });
}

/**
 * Shared query client instance.
 */
export const queryClient = createQueryClient();