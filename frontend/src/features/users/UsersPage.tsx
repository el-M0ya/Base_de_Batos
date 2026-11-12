/**
 * Página de administración de usuarios (E4-06).
 *
 * @remarks
 * Combina el listado de usuarios (`UsersContainer`) con el formulario de
 * creación (`UserFormContainer`). Es el componente que se registra en la ruta
 * `/users` de `app/routes.tsx`, protegido por el route guard para el rol
 * `administrator`.
 */
import { useState } from 'react';
import { UsersContainer } from './UsersContainer';
import { UserFormContainer } from './UserFormContainer';

/**
 * Página de administración de usuarios.
 */
export function UsersPage() {
  const [showForm, setShowForm] = useState(false);

  return (
    <section className="users-page">
      <UsersContainer />

      {showForm && (
        <div className="users-page__form-wrapper">
          <UserFormContainer onCancel={() => setShowForm(false)} />
        </div>
      )}

      <button
        className="users-page__create-button"
        onClick={() => setShowForm(true)}
      >
        Crear cuenta
      </button>
    </section>
  );
}
