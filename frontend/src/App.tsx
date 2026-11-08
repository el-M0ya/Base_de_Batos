import { LoginPage } from './features/auth/LoginPage';

/**
 * Root component of the application.
 *
 * @remarks
 * Temporarily shows the login screen directly. In E3-05 it is replaced by
 * the router with the layout and role-based navigation.
 */
export function App() {
  return <LoginPage />;
}
