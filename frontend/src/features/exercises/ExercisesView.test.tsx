import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { AuthenticatedUser } from '../../shared/types/roles';
import type { Exercise, ExerciseClassificationInput } from './types';
import { ExercisesView } from './ExercisesView';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useExercises: vi.fn(),
  useUpdateExerciseClassification: vi.fn(),
}));

vi.mock('../../shared/auth/useAuth', () => ({ useAuth: mocks.useAuth }));
vi.mock('./useExercises', () => ({
  useExercises: mocks.useExercises,
  useUpdateExerciseClassification: mocks.useUpdateExerciseClassification,
}));
vi.mock('./ExerciseTable', () => ({
  ExerciseTable: ({
    exercises,
    onReclassify,
  }: {
    exercises: Exercise[];
    onReclassify: (exercise: Exercise) => void;
  }) => (
    <div data-testid="exercise-table">
      {exercises.map((exercise) => (
        <span key={exercise.id}>
          {exercise.name}
          <button type="button" onClick={() => onReclassify(exercise)}>
            Reclasificar {exercise.name}
          </button>
        </span>
      ))}
    </div>
  ),
}));
vi.mock('./ExerciseForm', () => ({
  ExerciseForm: ({
    backendError,
    onCancel,
    onSubmit,
  }: {
    backendError?: Error | null;
    onCancel: () => void;
    onSubmit: (input: ExerciseClassificationInput) => Promise<void>;
  }) => (
    <div data-testid="exercise-form">
      {backendError !== null && backendError !== undefined && (
        <p role="alert">{backendError.message}</p>
      )}
      <button
        type="button"
        onClick={() =>
          void onSubmit({
            muscleGroupId: '2',
            exerciseType: 'cardio',
            intensity: 'alto',
          })
        }
      >
        Guardar cambios
      </button>
      <button type="button" onClick={onCancel}>
        Cancelar
      </button>
    </div>
  ),
}));

const exercise: Exercise = {
  id: 'exercise-1',
  name: 'Press de banca',
  description: 'Trabajo de fuerza.',
  exerciseType: 'fuerza',
  intensity: 'medio',
  muscleGroupId: '1',
  muscleGroupName: 'Pecho',
  trainerId: 'trainer-1',
  registrationDate: '2026-01-15',
};

const trainer = (id: string, role: AuthenticatedUser['role'] = 'trainer'): AuthenticatedUser => ({
  id,
  email: `${id}@example.com`,
  role,
  capabilities: { can_generate: true, can_validate: false },
});

const queryState = {
  data: [exercise],
  isLoading: false,
  error: null,
};

const mutationState = {
  error: null as Error | null,
  isPending: false,
  mutateAsync: vi.fn().mockResolvedValue(exercise),
};

beforeEach(() => {
  queryState.data = [exercise];
  mutationState.error = null;
  mutationState.mutateAsync.mockClear();
});

function renderView(user: AuthenticatedUser | null = trainer('trainer-1')) {
  mocks.useAuth.mockReturnValue({ user });
  mocks.useExercises.mockReturnValue(queryState);
  mocks.useUpdateExerciseClassification.mockReturnValue(mutationState);
  return render(<ExercisesView />);
}

describe('ExercisesView', () => {
  it('renders the exercise list', () => {
    renderView();

    expect(screen.getByTestId('exercise-table')).toHaveTextContent('Press de banca');
  });

  it('opens the form only for the creating trainer', async () => {
    const user = userEvent.setup();
    const firstRender = renderView(trainer('trainer-1'));
    await user.click(screen.getByRole('button', { name: 'Reclasificar Press de banca' }));
    expect(screen.getByTestId('exercise-form')).toBeInTheDocument();

    firstRender.unmount();
    renderView(trainer('trainer-2'));
    await user.click(screen.getByRole('button', { name: 'Reclasificar Press de banca' }));
    expect(screen.queryByTestId('exercise-form')).not.toBeInTheDocument();
  });

  it('executes the mutation and closes the form after success', async () => {
    const user = userEvent.setup();
    renderView();
    await user.click(screen.getByRole('button', { name: 'Reclasificar Press de banca' }));
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    await waitFor(() =>
      expect(mutationState.mutateAsync).toHaveBeenCalledWith({
        id: 'exercise-1',
        input: {
          muscleGroupId: '2',
          exerciseType: 'cardio',
          intensity: 'alto',
        },
      }),
    );
    expect(screen.queryByTestId('exercise-form')).not.toBeInTheDocument();
  });

  it('renders updated query data after a successful mutation without a full reload', async () => {
    const user = userEvent.setup();
    const view = renderView();
    await user.click(screen.getByRole('button', { name: 'Reclasificar Press de banca' }));
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }));
    await waitFor(() => expect(mutationState.mutateAsync).toHaveBeenCalled());

    queryState.data = [{ ...exercise, name: 'Press de banca actualizado' }];
    view.rerender(<ExercisesView />);
    expect(screen.getByTestId('exercise-table')).toHaveTextContent('Press de banca actualizado');
  });

  it('passes backend errors to the form', async () => {
    const user = userEvent.setup();
    mutationState.error = new Error('No tienes permiso para reclasificar este ejercicio.');
    renderView();
    await user.click(screen.getByRole('button', { name: 'Reclasificar Press de banca' }));

    expect(screen.getByRole('alert')).toHaveTextContent(
      'No tienes permiso para reclasificar este ejercicio.',
    );
  });
});
