/**
 * Vista presentacional del listado de usuarios (E4-06).
 *
 * @remarks
 * Recibe todo por `props`: no llama a la API, no usa rutas ni contexto global.
 * Renderiza una tabla ordenable con `DataTable`, un botón para crear cuenta y
 * acciones de desactivar por fila. El contenedor (`UsersContainer`) provee los
 * datos y manejadores.
 */
import type { UserAccount } from '../../shared/types/users';
import type { ColumnDef } from '../../shared/components/DataTable/columns';
import { DataTable } from '../../shared/components/DataTable/DataTable';
import { Button } from '../../shared/components/Button';
import { messages } from '../../shared/i18n/messages';

/**
 * Props de `UsersView`.
 */
export interface UsersViewProps {
  /** Lista de cuentas de usuario. */
  users: UserAccount[];
  /** `true` mientras se carga o guarda información. */
  loading: boolean;
  /** Mensaje de error o `null`. */
  error: string | null;
  /** Manejador para recargar la lista. */
  onReload: () => void;
  /** Manejador para desactivar una cuenta. */
  onDeactivate: (id: number) => void;
  /** Manejador para abrir el formulario de edición. */
  onEdit: (user: UserAccount) => void;
}

/**
 * Formatea el rol para mostrarlo en la tabla.
 */
function formatRole(value: string | number | undefined): string {
  const labels: Record<string, string> = {
    administrator: messages.users.form.roleAdministrator,
    trainer: messages.users.form.roleTrainer,
    client: messages.users.form.roleClient,
  };
  return labels[String(value)] ?? String(value ?? '');
}

/**
 * Formatea el estado para mostrarlo en la tabla.
 */
function formatStatus(value: string | number | undefined): string {
  const labels: Record<string, string> = {
    active: messages.users.status.active,
    inactive: messages.users.status.inactive,
  };
  return labels[String(value)] ?? String(value ?? '');
}

/**
 * Vista del listado de usuarios.
 */
export function UsersView({
  users,
  loading,
  error,
  onReload,
  onDeactivate,
  onEdit,
}: UsersViewProps) {
  const columns: ColumnDef<UserAccount>[] = [
    {
      accessor: 'email',
      header: messages.users.table.email,
      sortable: true,
    },
    {
      accessor: 'role',
      header: messages.users.table.role,
      sortable: true,
      format: (value: unknown) => formatRole(value as string | number | undefined),
    },
    {
      accessor: 'status',
      header: messages.users.table.status,
      sortable: true,
      format: (value: unknown) => formatStatus(value as string | number | undefined),
    },
    {
      accessor: 'id',
      header: messages.users.table.actions,
      sortable: false,
      format: () => '',
    },
  ];

  return (
    <section className="users-view">
      <header className="users-view__header">
        <h1 className="users-view__title">{messages.users.title}</h1>
      </header>

      {error && (
        <div className="users-view__error" role="alert">
          {error}
          <button type="button" className="users-view__error-dismiss" onClick={onReload}>
            {messages.users.dismissError}
          </button>
        </div>
      )}

      <DataTable
        columns={columns as unknown as ColumnDef<Record<string, unknown>>[]}
        data={users as unknown as Record<string, unknown>[]}
        loading={loading}
      />

      <div className="users-view__actions">
        {users.map((user) => (
          <div key={user.id} className="users-view__action-row">
            <span className="users-view__action-email">{user.email}</span>
            <Button variant="secondary" onClick={() => onDeactivate(user.id)} isLoading={loading}>
              {user.status === 'active'
                ? messages.users.deactivateButton
                : messages.users.activateButton}
            </Button>
            <Button variant="secondary" onClick={() => onEdit(user)} isLoading={loading}>
              {messages.users.editButton}
            </Button>
          </div>
        ))}
      </div>
    </section>
  );
}
