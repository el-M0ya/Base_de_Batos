import { useState } from 'react';
import { Plus } from 'lucide-react';
import { ApiError } from '../../shared/api/apiError';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { Modal } from '../../shared/components/Modal';
import { useMuscleGroups } from '../../shared/hooks/useMuscleGroups';
import { TrainingProgramForm } from './TrainingProgramForm';
import { TrainingProgramTable } from './TrainingProgramTable';
import {
  useCreateTrainingProgram,
  useDeleteTrainingProgram,
  useTrainingPrograms,
  useUpdateTrainingProgram,
} from './useTrainingPrograms';
import type { TrainingProgram, TrainingProgramInput } from './types';
import { messages } from '../../shared/i18n/messages';
import styles from './TrainingProgramsView.module.css';

const t = messages.trainingPrograms;
const common = messages.common;

/**
 * Main CRUD view for training-program administration.
 *
 * @remarks
 * The view coordinates program mutations and the muscle-group options query,
 * while form, association editor and table remain reusable components.
 */
export function TrainingProgramsView() {
  const programsQuery = useTrainingPrograms();
  const muscleGroupsQuery = useMuscleGroups();
  const createMutation = useCreateTrainingProgram();
  const updateMutation = useUpdateTrainingProgram();
  const deleteMutation = useDeleteTrainingProgram();
  const [editingProgram, setEditingProgram] = useState<TrainingProgram>();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [deletingProgram, setDeletingProgram] = useState<TrainingProgram>();
  const [operationError, setOperationError] = useState<string>();

  const programs = programsQuery.data ?? [];
  const isSaving = createMutation.isPending || updateMutation.isPending;

  /** Opens the empty create form. */
  function openCreateForm() {
    setEditingProgram(undefined);
    setOperationError(undefined);
    setIsFormOpen(true);
  }

  /** Opens the edit form with the selected program. */
  function openEditForm(program: TrainingProgram) {
    setEditingProgram(program);
    setOperationError(undefined);
    setIsFormOpen(true);
  }

  /** Persists a new or edited program. */
  async function saveProgram(input: TrainingProgramInput) {
    if (editingProgram === undefined) {
      await createMutation.mutateAsync(input);
    } else {
      await updateMutation.mutateAsync({ id: editingProgram.id, input });
    }
    setIsFormOpen(false);
  }

  /** Deletes the selected program and exposes server failures. */
  async function deleteProgram() {
    if (deletingProgram === undefined) return;
    try {
      await deleteMutation.mutateAsync(deletingProgram.id);
      setDeletingProgram(undefined);
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

      {programsQuery.error !== null && programsQuery.error !== undefined && (
        <Alert>
          {programsQuery.error instanceof ApiError ? programsQuery.error.message : t.loadError}
        </Alert>
      )}
      {operationError !== undefined && (
        <Alert onDismiss={() => setOperationError(undefined)}>{operationError}</Alert>
      )}

      <section className={styles.content} aria-label={t.listLabel}>
        <TrainingProgramTable
          data={programs}
          isLoading={programsQuery.isLoading}
          onEdit={openEditForm}
          onDelete={setDeletingProgram}
        />
      </section>

      <Modal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        title={editingProgram === undefined ? t.form.createTitle : t.form.editTitle}
      >
        <TrainingProgramForm
          key={editingProgram?.id ?? 'new-training-program'}
          initialValue={editingProgram}
          muscleGroups={muscleGroupsQuery.data ?? []}
          isLoadingMuscleGroups={muscleGroupsQuery.isLoading}
          muscleGroupsError={muscleGroupsQuery.error}
          onSubmit={saveProgram}
          onCancel={() => setIsFormOpen(false)}
          isSubmitting={isSaving}
        />
      </Modal>

      <Modal
        isOpen={deletingProgram !== undefined}
        onClose={() => setDeletingProgram(undefined)}
        title={t.delete.title}
        footer={
          <div className={styles.confirmActions}>
            <Button variant="secondary" onClick={() => setDeletingProgram(undefined)}>
              {common.cancel}
            </Button>
            <Button
              onClick={() => void deleteProgram()}
              isLoading={deleteMutation.isPending}
              className={styles.deleteButton}
            >
              {common.delete}
            </Button>
          </div>
        }
      >
        {t.delete.confirmBefore}
        <strong>{deletingProgram?.name}</strong>
        {t.delete.confirmAfter}
      </Modal>
    </main>
  );
}
