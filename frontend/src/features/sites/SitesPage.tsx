import { SitesView } from './SitesView';

/**
 * Route-level entry point for gym-site administration.
 *
 * @remarks
 * The QueryClient provider is composed once in `App.tsx`.
 */
export function SitesPage() {
  return <SitesView />;
}
