/**
 * Tests for the session storage in `sessionStorage` (E4-05).
 */
import { beforeEach, describe, expect, it } from 'vitest';
import type { AuthenticatedUser } from '../types/roles';
import { sessionStore } from './sessionStore';

const USER: AuthenticatedUser = {
  id: '7',
  email: 'chief@gym.test',
  role: 'trainer',
  capabilities: { can_generate: true, can_validate: true },
};

beforeEach(() => {
  sessionStorage.clear();
});

describe('sessionStore', () => {
  it('guarda, lee y borra el token y el usuario', () => {
    sessionStore.save('jwt-123', USER);

    expect(sessionStore.readToken()).toBe('jwt-123');
    expect(sessionStore.readUser()).toEqual(USER);

    sessionStore.clear();

    expect(sessionStore.readToken()).toBeNull();
    expect(sessionStore.readUser()).toBeNull();
  });

  it('devuelve null si el usuario guardado está dañado', () => {
    sessionStorage.setItem('forjafit:user', '{esto no es JSON');

    expect(sessionStore.readUser()).toBeNull();
  });

  it('marca, consulta y borra la sesión expirada', () => {
    expect(sessionStore.hasExpired()).toBe(false);

    sessionStore.markExpired();

    expect(sessionStore.hasExpired()).toBe(true);
    expect(sessionStore.hasExpired()).toBe(true); // checking does not clear it

    sessionStore.clearExpired();

    expect(sessionStore.hasExpired()).toBe(false);
  });
});
