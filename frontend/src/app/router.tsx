/**
 * Enrutador de la aplicación (E3-05).
 *
 * @remarks
 * Selecciona `BrowserRouter` en operación normal y `HashRouter` cuando el modo
 * simulado está activo (`VITE_API_MODE=mock`), de modo que la demo estática en
 * GitHub Pages sobreviva a una recarga de página. Declara las rutas a partir
 * del registro único de `routes.ts`, protegiendo cada una con `RouteGuard`
 * excepto las públicas (`/login`). La sesión se provee desde `AuthProvider` en
 * `App.tsx`.
 */
import { BrowserRouter, HashRouter, Routes, Route } from 'react-router-dom';
import { useAuth } from '../shared/auth/useAuth';
import { AppLayout } from './AppLayout';
import { LoginPage } from '../features/auth/LoginPage';
import { routes } from './routes';
import { RouteGuard } from './RouteGuard';

/** En modo simulado se usa el enrutador de hash para la demo estática. */
const useHashRouter = import.meta.env.VITE_API_MODE === 'mock';

/**
 * Componente raíz del enrutado.
 *
 * @remarks
 * Mientras se resuelve la sesión (`isLoading`) muestra un texto de carga. Una
 * vez lista, renderiza el `Router` elegido: `/login` es público y el resto de
 * rutas heredan `AppLayout` y se protegen con `RouteGuard` según rol o
 * capacidad.
 */
export function Router() {
  const RouterComponent = useHashRouter ? HashRouter : BrowserRouter;
  const { isLoading } = useAuth();

  if (isLoading) {
    return <div data-testid="router-loading">Cargando…</div>;
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
                route.path === '/'
                  ? 'index'
                  : route.path === '*'
                    ? '*'
                    : route.path.slice(1);
              return (
                <Route
                  key={route.path}
                  path={path}
                  element={
                    route.public
                      ? <Element />
                      : (
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

export default Router;
