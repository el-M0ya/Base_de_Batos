/**
 * Contenedor del listado de usuarios (E4-06).
 *
 * @remarks
 * Orquesta `useUsers` (acceso a datos) y `UsersView` (presentación). Es el
 * único componente de esta pantalla que conoce la API y los manejadores de
 * eventos; la vista recibe todo por `props`. Respeta la arquitectura
 * Container / Presentational y la regla de que una feature no importa de otra.
 *
 * Solo el administrador debe renderizar este contenedor (el route guard lo
 * impone en `app/routes.tsx`).
 */
import { useState } from 'react';
import { useUsers } from './useUsers';
import { UsersView } from './UsersView';
import type { UserAccount, UpdateUserInput } from '../../shared/types/users';
import { messages } from '../../shared/i18n/messages';

const t = messages.users;
const common = messages.common;

/**
 * Contenedor del listado de usuarios.
 *
 * @remarks
 * Gestiona la edición de cuentas a través del hook `useUsers`. La edición se
 * muestra en un panel lateral dentro del mismo contenedor. La creación de
 * cuentas nuevas se hace desde `UserFormContainer`, renderizado por
 * `UsersPage`.
 */
export function UsersContainer() {
  const { users, loading, error, reload, updateUser, deactivateUser } = useUsers();

  const [editingUser, setEditingUser] = useState<UserAccount | null>(null);

  function handleEdit(user: UserAccount) {
    setEditingUser(user);
  }

  function handleCancel() {
    setEditingUser(null);
  }

  async function handleSave() {
    if (!editingUser) {
      return;
    }

    const input: UpdateUserInput = {};
    if (editingUser.trainerProfile?.specialty !== undefined) {
      input.specialty = editingUser.trainerProfile.specialty;
    }
    if (editingUser.clientProfile?.age !== undefined) {
      input.age = editingUser.clientProfile.age;
    }
    if (editingUser.clientProfile?.idSite !== undefined) {
      input.idSite = editingUser.clientProfile.idSite;
    }

    const saved = await updateUser(editingUser.id, input);
    if (saved) {
      setEditingUser(null);
    }
  }

  async function handleDeactivate(id: number) {
    if (!window.confirm(t.deactivateConfirm)) {
      return;
    }
    await deactivateUser(id);
  }

  return (
    <section className="users-container">
      <UsersView
        users={users}
        loading={loading}
        error={error}
        onReload={reload}
        onDeactivate={handleDeactivate}
        onEdit={handleEdit}
      />

      {editingUser && (
        <aside className="users-container__edit-panel">
          <h2>{t.editPanelTitle(editingUser.email)}</h2>
          <p>{editingUser.role}</p>
          <p>{editingUser.status === 'active' ? t.status.active : t.status.inactive}</p>
          <button className="save-button" onClick={handleSave} disabled={loading}>
            {common.saveChanges}
          </button>
          <button className="cancel-button" onClick={handleCancel}>
            {common.cancel}
          </button>
        </aside>
      )}
    </section>
  );
}
