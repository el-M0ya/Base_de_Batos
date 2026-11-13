/**
 * Hash paths supported by the application.
 *
 * @remarks
 * Keeping route identifiers in `app/` gives navigation links and the router
 * one source of truth without making features depend on one another.
 */
export const appRoutes = {
  login: '/login',
  sites: '/admin/sites',
  trainingPrograms: '/admin/training-programs',
  muscleGroups: '/admin/muscle-groups',
} as const;
