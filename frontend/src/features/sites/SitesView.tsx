import { useState } from 'react';
import { Plus } from 'lucide-react';
import { ApiError } from '../../shared/api/apiError';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { Modal } from '../../shared/components/Modal';
import { SiteForm } from './SiteForm';
import { SiteTable } from './SiteTable';
import { useCreateSite, useDeleteSite, useSites, useUpdateSite } from './useSites';
import type { Site, SiteInput } from './types';
import styles from './SitesView.module.css';

/**
 * Main CRUD view for the gym-site administration module.
 *
 * @remarks
 * TanStack Query state is orchestrated here while the form and table remain
 * reusable presentational components.
 */
export function SitesView() {
  const sitesQuery = useSites();
  const createMutation = useCreateSite();
  const updateMutation = useUpdateSite();
  const deleteMutation = useDeleteSite();
  const [editingSite, setEditingSite] = useState<Site>();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [deletingSite, setDeletingSite] = useState<Site>();
  const [operationError, setOperationError] = useState<string>();

  const sites = sitesQuery.data ?? [];
  const isSaving = createMutation.isPending || updateMutation.isPending;

  /** Opens an empty form for a new site. */
  function openCreateForm() {
    setEditingSite(undefined);
    setOperationError(undefined);
    setIsFormOpen(true);
  }

  /** Opens the form populated with the selected site. */
  function openEditForm(site: Site) {
    setEditingSite(site);
    setOperationError(undefined);
    setIsFormOpen(true);
  }

  /** Saves a site through the appropriate create or update mutation. */
  async function saveSite(input: SiteInput) {
    if (editingSite === undefined) {
      await createMutation.mutateAsync(input);
    } else {
      await updateMutation.mutateAsync({ id: editingSite.id, input });
    }
    setIsFormOpen(false);
  }

  /** Deletes the selected site and exposes server failures to the user. */
  async function deleteSite() {
    if (deletingSite === undefined) return;
    try {
      await deleteMutation.mutateAsync(deletingSite.id);
      setDeletingSite(undefined);
    } catch (error) {
      setOperationError(error instanceof ApiError ? error.message : 'No se pudo eliminar el sitio.');
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Administración</p>
          <h1 className={styles.title}>Sitios de gimnasios</h1>
          <p className={styles.subtitle}>Gestiona las sedes donde se desarrollan los entrenamientos.</p>
        </div>
        <Button icon={<Plus size={18} aria-hidden="true" />} onClick={openCreateForm}>
          Nuevo sitio
        </Button>
      </header>

      {sitesQuery.error !== null && sitesQuery.error !== undefined && (
        <Alert>
          {sitesQuery.error instanceof ApiError
            ? sitesQuery.error.message
            : 'No se pudo cargar el catálogo de sitios.'}
        </Alert>
      )}
      {operationError !== undefined && (
        <Alert onDismiss={() => setOperationError(undefined)}>{operationError}</Alert>
      )}

      <section className={styles.content} aria-label="Listado de sitios de gimnasios">
        <SiteTable
          data={sites}
          isLoading={sitesQuery.isLoading}
          onEdit={openEditForm}
          onDelete={setDeletingSite}
        />
      </section>

      <Modal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        title={editingSite === undefined ? 'Nuevo sitio' : 'Editar sitio'}
      >
        <SiteForm
          key={editingSite?.id ?? 'new-site'}
          initialValue={editingSite}
          onSubmit={saveSite}
          onCancel={() => setIsFormOpen(false)}
          isSubmitting={isSaving}
        />
      </Modal>

      <Modal
        isOpen={deletingSite !== undefined}
        onClose={() => setDeletingSite(undefined)}
        title="Eliminar sitio"
        footer={
          <div className={styles.confirmActions}>
            <Button variant="secondary" onClick={() => setDeletingSite(undefined)}>
              Cancelar
            </Button>
            <Button
              onClick={() => void deleteSite()}
              isLoading={deleteMutation.isPending}
              className={styles.deleteButton}
            >
              Eliminar
            </Button>
          </div>
        }
      >
        ¿Seguro que deseas eliminar <strong>{deletingSite?.name}</strong>? Esta acción no se puede deshacer.
      </Modal>
    </main>
  );
}
