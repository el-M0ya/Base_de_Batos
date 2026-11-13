import { useEffect, useState } from 'react';
import { MuscleGroupsPage } from '../features/muscle-groups/MuscleGroupsPage';
import { SitesPage } from '../features/sites/SitesPage';
import { TrainingProgramsPage } from '../features/training-programs/TrainingProgramsPage';
import { ExercisesPage } from '../features/exercises/ExercisesPage';
import { LoginPage } from '../features/auth/LoginPage';
import { AdminLayout } from './layouts/AdminLayout';
import ProtectedRoute from '../shared/auth/ProtectedRoute';
import { appRoutes } from './routes';

/** Normalizes the browser hash into a route path. */
function readPath(): string {
  const hash = window.location.hash.replace(/^#/, '');
  return hash === '' ? appRoutes.login : hash;
}

/**
 * Changes the current hash route without requiring a routing dependency.
 *
 * @param path - Route path without the leading hash.
 */
/**
 * Resolves the current hash to a page and global layout.
 *
 * @remarks
 * Hash routing keeps these pages compatible with static hosting and full
 * reloads. Feature components are imported by `app/`, never by one another.
 */
export function AppRouter() {
  const [path, setPath] = useState(readPath);

  useEffect(() => {
    /** Updates React state after browser back/forward or a navigation link. */
    function handleHashChange() {
      setPath(readPath());
    }

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  if (path === appRoutes.login) return <LoginPage />;

  if (path === appRoutes.sites) {
    return (
      <AdminLayout currentPath={path}>
        <SitesPage />
      </AdminLayout>
    );
  }

  if (path === appRoutes.trainingPrograms) {
    return (
      <AdminLayout currentPath={path}>
        <TrainingProgramsPage />
      </AdminLayout>
    );
  }

  if (path === appRoutes.muscleGroups) {
    return (
      <AdminLayout currentPath={path}>
        <MuscleGroupsPage />
      </AdminLayout>
    );
  }

  if (path === appRoutes.exercises) {
    return (
      <ProtectedRoute>
        <AdminLayout currentPath={path}>
          <ExercisesPage />
        </AdminLayout>
      </ProtectedRoute>
    );
  }

  return (
    <AdminLayout currentPath={appRoutes.sites}>
      <section>
        <h1>Página no encontrada</h1>
        <p>La ruta solicitada no existe.</p>
        <a href={`#${appRoutes.sites}`}>Ir a sitios</a>
      </section>
    </AdminLayout>
  );
}
