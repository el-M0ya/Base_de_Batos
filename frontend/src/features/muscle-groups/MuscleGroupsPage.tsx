import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../../shared/api/queryClient';
import { MuscleGroupsView } from './MuscleGroupsView';

/**
 * Route-level entry point for the muscle-group administration screen.
 *
 * @remarks
 * The provider is kept in this page wrapper so the view can be embedded in
 * the current application before the global router/provider composition lands.
 */
export function MuscleGroupsPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <MuscleGroupsView />
    </QueryClientProvider>
  );
}
