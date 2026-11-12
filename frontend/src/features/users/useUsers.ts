/**
 * Hook para consultar y gestionar cuentas de usuario (E4-06).
 *
 * @remarks
 * Encapsula el acceso a la API de usuarios a través de `usersApi`, de modo
 * que los componentes solo dependen de este hook y no de la implementación
 * concreta (mock o real). Maneja estados de carga, datos y errores.
 *
 * Toda la lógica de acceso a datos vive en este hook, respetando la regla de
 * que los componentes `*View` reciben todo por `props` y no llaman a la API.
 */
import { useState, useEffect } from 'react';
import { usersApi, getApiErrorMessage } from './api';
import type { UserAccount } from '../../shared/types/users';

/**
 * Valor devuelto por `useUsers`.
 */
export interface UseUsersReturn {
  /** Lista de cuentas de usuario. */
  users: UserAccount[];
  /** `true` mientras se carga o guarda información. */
  loading: boolean;
  /** Mensaje de error de la última operación, o `null`. */
  error: string | null;
  /** Recarga la lista de usuarios desde la API. */
  reload: () => Promise<void>;
  /** Crea una nueva cuenta. */
  createUser: (
    input: Parameters<typeof usersApi.createUser>[0],
  ) => Promise<UserAccount | null>;
  /** Modifica una cuenta existente. */
  updateUser: (
    id: number,
    input: Parameters<typeof usersApi.updateUser>[1],
  ) => Promise<UserAccount | null>;
  /** Desactiva una cuenta (baja lógica). */
  deactivateUser: (id: number) => Promise<boolean>;
}

/**
 * Hook para consultar y gestionar cuentas de usuario.
 *
 * @returns Estado y operaciones para administrar usuarios.
 */
export function useUsers(): UseUsersReturn {
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Carga la lista de usuarios desde la API. */
  async function loadUsers(): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const result = await usersApi.listUsers();
      if (result.ok) {
        setUsers(result.data);
      } else {
        setError(getApiErrorMessage(result) ?? 'No se pudieron cargar los usuarios.');
      }
    } catch {
      setError('No se pudieron cargar los usuarios.');
    } finally {
      setLoading(false);
    }
  }

  // Carga los usuarios al montar el hook.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadUsers();
  }, []);

  async function createUser(
    input: Parameters<typeof usersApi.createUser>[0],
  ): Promise<UserAccount | null> {
    setLoading(true);
    setError(null);
    try {
      const result = await usersApi.createUser(input);
      if (result.ok) {
        setUsers((prev) => [...prev, result.data]);
        return result.data;
      }
      setError(getApiErrorMessage(result) ?? 'No se pudo crear la cuenta.');
      return null;
    } catch {
      setError('No se pudo crear la cuenta.');
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function updateUser(
    id: number,
    input: Parameters<typeof usersApi.updateUser>[1],
  ): Promise<UserAccount | null> {
    setLoading(true);
    setError(null);
    try {
      const result = await usersApi.updateUser(id, input);
      if (result.ok) {
        setUsers((prev) =>
          prev.map((u) => (u.id === id ? result.data : u)),
        );
        return result.data;
      }
      setError(getApiErrorMessage(result) ?? 'No se pudo modificar la cuenta.');
      return null;
    } catch {
      setError('No se pudo modificar la cuenta.');
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function deactivateUser(id: number): Promise<boolean> {
    setLoading(true);
    setError(null);
    try {
      const result = await usersApi.deactivateUser(id);
      if (result.ok) {
        setUsers((prev) =>
          prev.map((u) => (u.id === id ? { ...u, status: 'inactive' } : u)),
        );
        return true;
      }
      setError(getApiErrorMessage(result) ?? 'No se pudo desactivar la cuenta.');
      return false;
    } catch {
      setError('No se pudo desactivar la cuenta.');
      return false;
    } finally {
      setLoading(false);
    }
  }

  return {
    users,
    loading,
    error,
    reload: loadUsers,
    createUser,
    updateUser,
    deactivateUser,
  };
}
