import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './shared/api/queryClient';
import { AuthProvider } from './shared/auth/AuthContext';
import { AppRouter } from './app/router';

/**
 * Root component of the application.
 *
 * @remarks
 * Composes the global providers once, so every page can rely on them:
 * `QueryClientProvider` (server-data cache used by the feature hooks) and
 * `AuthProvider` (session). Then mounts `AppRouter`, which owns the
 * application shell, the navigation and the role-protected routes.
 */
export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
