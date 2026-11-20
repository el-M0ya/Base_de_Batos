/**
 * Application router (E3-05).
 *
 * @remarks
 * Uses `BrowserRouter` in normal operation and `HashRouter` when the mock mode
 * is active (`VITE_API_MODE=mock`), so the static demo on GitHub Pages survives
 * a page reload. Routes are declared from the single registry in `routes.tsx`
 * and every non-public route is protected by `RouteGuard`. The session comes
 * from `AuthProvider` in `App.tsx`.
 */
import { BrowserRouter, HashRouter, Routes, Route } from 'react-router-dom';
import { useAuth } from '../shared/auth/useAuth';
import { AppLayout } from './AppLayout';
import { LoginPage } from '../features/auth/LoginPage';
import { routes } from './routes';
import { RouteGuard } from './RouteGuard';
import { messages } from '../shared/i18n/messages';

/** In mock mode the hash router is used for the static demo. */
const useHashRouter = import.meta.env.VITE_API_MODE === 'mock';

/**
 * Root routing component.
 *
 * @remarks
 * While the session is being restored (`isLoading`) it shows a loading text.
 * Once ready, `/login` is public and every other route is rendered inside
 * `AppLayout` and guarded by role or capability.
 */
export function AppRouter() {
  const RouterComponent = useHashRouter ? HashRouter : BrowserRouter;
  const { isLoading } = useAuth();

  if (isLoading) {
    return <div data-testid="router-loading">{messages.states.loading}</div>;
  }

  return (
    <RouterComponent>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<AppLayout />}>
          {routes
            .filter((route) => route.path !== '/login')
            .map((route) => {
              const Element = route.element;
              const path =
                route.path === '/' ? 'index' : route.path === '*' ? '*' : route.path.slice(1);
              return (
                <Route
                  key={route.path}
                  path={path}
                  element={
                    route.public ? (
                      <Element />
                    ) : (
                      <RouteGuard
                        roles={route.roles}
                        capabilities={route.capabilities}
                        element={<Element />}
                      />
                    )
                  }
                />
              );
            })}
        </Route>
      </Routes>
    </RouterComponent>
  );
}
