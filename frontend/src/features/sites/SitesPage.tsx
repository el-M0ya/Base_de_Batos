import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../../shared/api/queryClient';
import { SitesView } from './SitesView';

/**
 * Route-level entry point for gym-site administration.
 *
 * @remarks
 * The provider is kept in this page wrapper until the global application
 * provider composition is introduced.
 */
export function SitesPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <SitesView />
    </QueryClientProvider>
  );
}
