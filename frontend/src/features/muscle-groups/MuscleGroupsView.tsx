import { useState } from 'react';
import { Plus } from 'lucide-react';
import { ApiError } from '../../shared/api/apiError';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { Modal } from '../../shared/components/Modal';
import {
  useCreateMuscleGroup,
  useDeleteMuscleGroup,
  useMuscleGroups,
  useUpdateMuscleGroup,
} from '../../shared/hooks/useMuscleGroups';
import { MuscleGroupForm } from './MuscleGroupForm';
import { MuscleGroupTable } from './MuscleGroupTable';
import type { MuscleGroup, MuscleGroupInput } from '../../shared/types/muscleGroup';
import { messages } from '../../shared/i18n/messages';
import styles from './MuscleGroupsView.module.css';

const t = messages.muscleGroups;
const common = messages.common;

/**
 * Presentational CRUD screen for the muscle-group catalog.
 *
 * @remarks
 * Query and mutation state is kept here while the form and table remain
 * presentational. The page wrapper supplies the QueryClient boundary.
 */
export function MuscleGroupsView() {
  const groupsQuery = useMuscleGroups();
  const createMutation = useCreateMuscleGroup();
  const updateMutation = useUpdateMuscleGroup();
  const deleteMutation = useDeleteMuscleGroup();
  const [editingGroup, setEditingGroup] = useState<MuscleGroup>();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [deletingGroup, setDeletingGroup] = useState<MuscleGroup>();
  const [operationError, setOperationError] = useState<string>();

  const groups = groupsQuery.data ?? [];
  const isSaving = createMutation.isPending || updateMutation.isPending;

  /** Opens the empty form for a new catalog record. */
  function openCreateForm() {
    setEditingGroup(undefined);
    setOperationError(undefined);
    setIsFormOpen(true);
  }

  /** Opens the form populated with the selected record. */
  function openEditForm(group: MuscleGroup) {
    setEditingGroup(group);
    setOperationError(undefined);
    setIsFormOpen(true);
  }

  /** Saves a new or existing record through the appropriate mutation. */
  async function saveGroup(input: MuscleGroupInput) {
    if (editingGroup === undefined) {
      await createMutation.mutateAsync(input);
    } else {
      await updateMutation.mutateAsync({ id: editingGroup.id, input });
    }
    setIsFormOpen(false);
  }

  /** Deletes the selected record and reports server failures. */
  async function deleteGroup() {
    if (deletingGroup === undefined) return;
    try {
      await deleteMutation.mutateAsync(deletingGroup.id);
      setDeletingGroup(undefined);
    } catch (error) {
      setOperationError(error instanceof ApiError ? error.message : t.deleteError);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>{common.adminEyebrow}</p>
          <h1 className={styles.title}>{t.title}</h1>
          <p className={styles.subtitle}>{t.subtitle}</p>
        </div>
        <Button icon={<Plus size={18} aria-hidden="true" />} onClick={openCreateForm}>
          {t.createButton}
        </Button>
      </header>

      {groupsQuery.error !== null && groupsQuery.error !== undefined && (
        <Alert>
          {groupsQuery.error instanceof ApiError ? groupsQuery.error.message : t.loadError}
        </Alert>
      )}
      {operationError !== undefined && (
        <Alert onDismiss={() => setOperationError(undefined)}>{operationError}</Alert>
      )}

      <section className={styles.content} aria-label={t.listLabel}>
        <MuscleGroupTable
          data={groups}
          isLoading={groupsQuery.isLoading}
          onEdit={openEditForm}
          onDelete={setDeletingGroup}
        />
      </section>

      <Modal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        title={editingGroup === undefined ? t.form.createTitle : t.form.editTitle}
      >
        <MuscleGroupForm
          key={editingGroup?.id ?? 'new-muscle-group'}
          initialValue={editingGroup}
          onSubmit={saveGroup}
          onCancel={() => setIsFormOpen(false)}
          isSubmitting={isSaving}
        />
      </Modal>

      <Modal
        isOpen={deletingGroup !== undefined}
        onClose={() => setDeletingGroup(undefined)}
        title={t.delete.title}
        footer={
          <div className={styles.confirmActions}>
            <Button variant="secondary" onClick={() => setDeletingGroup(undefined)}>
              {common.cancel}
            </Button>
            <Button
              onClick={() => void deleteGroup()}
              isLoading={deleteMutation.isPending}
              className={styles.deleteButton}
            >
              {common.delete}
            </Button>
          </div>
        }
      >
        {t.delete.confirmBefore}
        <strong>{deletingGroup?.name}</strong>
        {t.delete.confirmAfter}
      </Modal>
    </main>
  );
}
