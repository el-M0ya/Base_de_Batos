/**
 * Pruebas unitarias del registro de rutas (`src/app/routes.ts`).
 *
 * @remarks
 * Cubre `isMenuEntryVisible` para cada combinación de rol y capacidad que
 * define el menú de navegación de E3-05.
 */
import { describe, expect, it } from 'vitest';
import type { MenuEntry } from './routes';
import { isMenuEntryVisible, menuEntries } from './routes';
import type { UserRole, UserCapabilities } from '../shared/types/roles';

function sessionWith(
  role: UserRole,
  capabilities: UserCapabilities,
): { hasRole: (r: UserRole) => boolean; hasCapability: (c: keyof UserCapabilities) => boolean } {
  return {
    hasRole: (r: UserRole) => r === role,
    hasCapability: (c: keyof UserCapabilities) => capabilities[c] === true,
  };
}

/** Devuelve la entrada de menú para una ruta, o lanza si no existe. */
function entryFor(path: string): MenuEntry {
  const entry = menuEntries.find((e) => e.path === path);
  if (!entry) {
    throw new Error(`No menu entry registered for path ${path}`);
  }
  return entry;
}

describe('isMenuEntryVisible', () => {
  it('muestra la ruta de inicio a cualquier usuario autenticado', () => {
    const home = entryFor('/');
    expect(
      isMenuEntryVisible(
        home,
        () => false,
        () => false,
      ),
    ).toBe(true);
  });

  it('entrenador ve Ejercicios y Rutinas, pero no administración', () => {
    const { hasRole, hasCapability } = sessionWith('trainer', {
      can_generate: true,
      can_validate: false,
    });

    const exercises = entryFor('/exercises');
    const routines = entryFor('/routines');
    const users = entryFor('/users');
    const reports = entryFor('/reports');

    expect(isMenuEntryVisible(exercises, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(routines, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(users, hasRole, hasCapability)).toBe(false);
    expect(isMenuEntryVisible(reports, hasRole, hasCapability)).toBe(true);
  });

  it('jefe de sala ve Ejercicios e Informes, pero no Rutinas sin can_generate', () => {
    const { hasRole, hasCapability } = sessionWith('trainer', {
      can_generate: false,
      can_validate: true,
    });

    const exercises = entryFor('/exercises');
    const routines = entryFor('/routines');

    expect(isMenuEntryVisible(exercises, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(routines, hasRole, hasCapability)).toBe(false);
  });

  it('cliente solo ve Inicio e Informes', () => {
    const { hasRole, hasCapability } = sessionWith('client', {
      can_generate: false,
      can_validate: false,
    });

    const home = entryFor('/');
    const reports = entryFor('/reports');
    const exercises = entryFor('/exercises');
    const users = entryFor('/users');

    expect(isMenuEntryVisible(home, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(reports, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(exercises, hasRole, hasCapability)).toBe(false);
    expect(isMenuEntryVisible(users, hasRole, hasCapability)).toBe(false);
  });

  it('administrador ve todas las entradas de administración', () => {
    const { hasRole, hasCapability } = sessionWith('administrator', {
      can_generate: false,
      can_validate: false,
    });

    const users = entryFor('/users');
    const sites = entryFor('/sites');
    const programs = entryFor('/programs');
    const muscleGroups = entryFor('/muscle-groups');

    expect(isMenuEntryVisible(users, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(sites, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(programs, hasRole, hasCapability)).toBe(true);
    expect(isMenuEntryVisible(muscleGroups, hasRole, hasCapability)).toBe(true);
  });
});
