import { AuthProvider } from './shared/auth/AuthContext';
import { LoginPage } from './features/auth/LoginPage';

/**
 * Root component of the application.
 *
 * @remarks
 * Wraps the app in `AuthProvider` so the session is available everywhere.
 * Temporarily shows the login screen directly. In E3-05 it is replaced by
 * the router with the layout and role-based navigation.
 */
export function App() {
  return (
    <AuthProvider>
      <LoginPage />
    </AuthProvider>
  );
}
