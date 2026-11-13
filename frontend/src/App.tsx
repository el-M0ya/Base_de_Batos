import { AuthProvider } from './shared/auth/AuthContext';
import { AppRouter } from './app/router';

/**
 * Root component of the application.
 *
 * @remarks
 * Wraps the app in `AuthProvider` so the session is available everywhere.
 * The application router owns hash-based page selection, while feature pages
 * remain isolated from one another and are composed by the app layer.
 */
export function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}
