/**
 * Registro único de rutas y entradas de navegación de la aplicación.
 *
 * @remarks
 * Este es el único archivo que declara qué rutas existen, a qué componente se
 * resuelven y qué rol o capacidad se requiere para cada una. Se sigue la regla
 * de navegación de E3-04: "la navegación se declara en un único archivo,
 * indicando qué rol o capacidad ve cada entrada".
 *
 * Las rutas de funcionalidades que aún no se implementan (ejercicios, rutinas,
 * informes, administración) apuntan a `ComingSoonView` y se conectarán a sus
 * componentes reales en las épocas correspondientes.
 */
import type { ComponentType } from 'react';
import { ComingSoonView } from './ComingSoonView';
import { DashboardView } from './DashboardView';
import { NotFoundView } from './NotFoundView';
import { LoginPage } from '../features/auth/LoginPage';
import { UsersPage } from '../features/users/UsersPage';
import { MuscleGroupsPage } from '../features/muscle-groups/MuscleGroupsPage';
import { SitesPage } from '../features/sites/SitesPage';
import { TrainingProgramsPage } from '../features/training-programs/TrainingProgramsPage';
import { messages } from '../shared/i18n/messages';
import type { UserRole } from '../shared/types/roles';
import type { UserCapabilities } from '../shared/types/roles';

/**
 * Entrada de una ruta registrada.
 */
export interface RouteDefinition {
  /** Ruta de la URL (por ejemplo, `/exercises`). */
  path: string;
  /** Componente que se renderiza en la ruta. */
  element: ComponentType;
  /** Etiqueta mostrada en el menú de navegación. */
  label: string;
  /** Roles que pueden ver/acceder a la ruta. Si se omite, cualquier usuario autenticado. */
  roles?: UserRole[] | undefined;
  /** Capacidades que se requieren (se satisface con cualquiera). */
  capabilities?: (keyof UserCapabilities)[] | undefined;
  /** Ruta pública (no requiere sesión). */
  public?: boolean;
}

/** Entrada del menú de navegación (sin componente, solo para mostrar). */
export interface MenuEntry {
  path: string;
  label: string;
  roles?: UserRole[] | undefined;
  capabilities?: (keyof UserCapabilities)[] | undefined;
}

/**
 * Rutas registradas. `*` es la ruta de no encontrado (404).
 */
export const routes: RouteDefinition[] = [
  {
    path: '/login',
    element: LoginPage,
    label: messages.nav.logout,
    public: true,
  },
  {
    path: '/',
    element: DashboardView,
    label: messages.nav.home,
  },
  {
    path: '/exercises',
    element: () => <ComingSoonView section="Ejercicios" />,
    label: messages.nav.exercises,
    roles: ['trainer', 'administrator'],
  },
  {
    path: '/routines',
    element: () => <ComingSoonView section="Rutinas" />,
    label: messages.nav.routines,
    roles: ['trainer'],
    capabilities: ['can_generate'],
  },
  {
    path: '/reports',
    element: () => <ComingSoonView section="Informes" />,
    label: messages.nav.reports,
  },
  {
    path: '/users',
    element: UsersPage,
    label: messages.nav.users,
    roles: ['administrator'],
  },
  {
    path: '/sites',
    element: SitesPage,
    label: messages.nav.sites,
    roles: ['administrator'],
  },
  {
    path: '/programs',
    element: TrainingProgramsPage,
    label: messages.nav.programs,
    roles: ['administrator'],
  },
  {
    path: '/muscle-groups',
    element: MuscleGroupsPage,
    label: messages.nav.muscleGroups,
    roles: ['administrator'],
  },
  {
    path: '*',
    element: NotFoundView,
    label: messages.notFound.title,
  },
] as const;

/** Entradas mostradas en el menú de navegación (sin la ruta de login ni 404). */
export const menuEntries: MenuEntry[] = routes
  .filter((route) => route.path !== '/login' && route.path !== '*')
  .map((route) => ({
    path: route.path,
    label: route.label,
    roles: route.roles,
    capabilities: route.capabilities,
  }));

/**
 * Indica si una entrada de navegación es visible para el usuario autenticado.
 *
 * @param entry - Entrada del menú a evaluar.
 * @param hasRole - Comprobación de rol de la sesión.
 * @param hasCapability - Comprobación de capacidad de la sesión.
 */
export function isMenuEntryVisible(
  entry: MenuEntry,
  hasRole: (role: UserRole) => boolean,
  hasCapability: (capability: keyof UserCapabilities) => boolean,
): boolean {
  const hasAnyRole = !entry.roles || entry.roles.some((role) => hasRole(role));
  const hasAnyCapability =
    !entry.capabilities || entry.capabilities.some((capability) => hasCapability(capability));
  return hasAnyRole && hasAnyCapability;
}
