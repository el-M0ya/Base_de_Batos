import { AuthProvider } from './shared/auth/AuthContext';
import { AppRouter } from './app/router';

/**
 * Root component of the application.
 *
 * @remarks
 * Wraps the app in `AuthProvider` so the session is available everywhere and
 * mounts `AppRouter`, which owns the application shell, the navigation and
 * the role-protected routes.
 */
export function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}

export default App;
