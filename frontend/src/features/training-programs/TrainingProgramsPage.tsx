import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../../shared/api/queryClient';
import { TrainingProgramsView } from './TrainingProgramsView';

/**
 * Route-level entry point for training-program administration.
 *
 * @remarks
 * The QueryClient provider remains local until global app providers are wired
 * into the application router.
 */
export function TrainingProgramsPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <TrainingProgramsView />
    </QueryClientProvider>
  );
}
