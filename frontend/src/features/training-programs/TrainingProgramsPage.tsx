import { TrainingProgramsView } from './TrainingProgramsView';

/**
 * Route-level entry point for training-program administration.
 *
 * @remarks
 * The QueryClient provider is composed once in `App.tsx`.
 */
export function TrainingProgramsPage() {
  return <TrainingProgramsView />;
}
