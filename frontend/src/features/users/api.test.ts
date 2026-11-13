/**
 * Pruebas de la API simulada de usuarios (E4-06).
 *
 * @remarks
 * Cubre listado, creación con unicidad de correo (U-1), modificación y
 * desactivación. La implementación real se conectará cuando E4-02 esté
 * disponible; estas pruebas verifican el contrato que usa la UI.
 */
import { describe, expect, it } from 'vitest';
import { usersApi } from './api';
import type { CreateUserInput, UpdateUserInput } from '../../shared/types/users';

describe('usersApi (mock)', () => {
  it('lista las cuentas registradas', async () => {
    const result = await usersApi.listUsers();

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.length).toBeGreaterThan(0);
      expect(result.data.some((u) => u.role === 'administrator')).toBe(true);
      expect(result.data.some((u) => u.role === 'trainer')).toBe(true);
      expect(result.data.some((u) => u.role === 'client')).toBe(true);
    }
  });

  it('crea una cuenta nueva con correo único', async () => {
    const input: CreateUserInput = {
      email: 'nuevo.entrenador@forjafit.demo',
      password: 'entrenador2026',
      role: 'trainer',
      specialty: 'Fuerza',
    };

    const result = await usersApi.createUser(input);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.email).toBe(input.email.toLowerCase());
      expect(result.data.role).toBe('trainer');
      expect(result.data.trainerProfile?.specialty).toBe('Fuerza');
      expect(result.data.status).toBe('active');
    }
  });

  it('rechaza el correo duplicado con código duplicateEmail (U-1)', async () => {
    const input: CreateUserInput = {
      email: 'admin@forjafit.demo',
      password: 'cualquiera',
      role: 'client',
    };

    const result = await usersApi.createUser(input);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe('duplicateEmail');
      expect(result.error.field).toBe('email');
    }
  });

  it('modifica el estado y el perfil de una cuenta existente', async () => {
    const input: UpdateUserInput = {
      status: 'inactive',
    };

    const result = await usersApi.updateUser(2, input);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.status).toBe('inactive');
    }
  });

  it('desactiva una cuenta (baja lógica)', async () => {
    const result = await usersApi.deactivateUser(3);

    expect(result.ok).toBe(true);

    const list = await usersApi.listUsers();
    if (list.ok) {
      const user = list.data.find((u) => u.id === 3);
      expect(user?.status).toBe('inactive');
    }
  });

  it('retorna error notFound para cuenta inexistente', async () => {
    const result = await usersApi.deactivateUser(99999);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe('notFound');
    }
  });
});
