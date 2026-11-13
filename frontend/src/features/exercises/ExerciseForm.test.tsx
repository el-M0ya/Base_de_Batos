import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ComponentProps } from 'react';
import { ExerciseForm } from './ExerciseForm';

const mocks = vi.hoisted(() => ({
  useExerciseCatalogs: vi.fn(),
}));

vi.mock('./useExercises', () => ({
  useExerciseCatalogs: mocks.useExerciseCatalogs,
}));

const exercise = {
  id: 'exercise-1',
  name: 'Press de banca',
  description: 'Trabajo de fuerza.',
  exerciseType: 'fuerza',
  intensity: 'medio',
  muscleGroupId: '1',
  muscleGroupName: 'Pecho',
  trainerId: 'trainer-1',
};

const catalogs = {
  muscleGroups: [
    { id: '1', name: 'Pecho', description: '' },
    { id: '2', name: 'Espalda', description: '' },
  ],
  exerciseTypes: ['fuerza', 'cardio'],
  intensityLevels: ['bajo', 'medio', 'alto'],
};

function renderForm(
  overrides: Partial<ComponentProps<typeof ExerciseForm>> = {},
  query: { data?: typeof catalogs; isLoading: boolean; error: Error | null } = {
    data: catalogs,
    isLoading: false,
    error: null,
  },
) {
  mocks.useExerciseCatalogs.mockReset();
  mocks.useExerciseCatalogs.mockReturnValue(query);
  const props = {
    exercise,
    onCancel: vi.fn(),
    onSubmit: vi.fn().mockResolvedValue(undefined),
    isSubmitting: false,
    backendError: null,
    ...overrides,
  };
  return { user: userEvent.setup(), props, ...render(<ExerciseForm {...props} />) };
}

describe('ExerciseForm', () => {
  it('loads catalog options', () => {
    renderForm();

    expect(screen.getByRole('option', { name: 'Espalda' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'cardio' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'alto' })).toBeInTheDocument();
  });

  it('shows the catalog loading state', () => {
    renderForm({}, { isLoading: true, error: null });

    expect(screen.getByRole('status')).toHaveTextContent('Cargando catálogos');
  });

  it('changes all three classification fields', async () => {
    const { user } = renderForm();

    await user.selectOptions(screen.getByLabelText('Grupo muscular'), '2');
    await user.selectOptions(screen.getByLabelText('Tipo de ejercicio'), 'cardio');
    await user.selectOptions(screen.getByLabelText('Intensidad'), 'alto');

    expect(screen.getByLabelText('Grupo muscular')).toHaveValue('2');
    expect(screen.getByLabelText('Tipo de ejercicio')).toHaveValue('cardio');
    expect(screen.getByLabelText('Intensidad')).toHaveValue('alto');
  });

  it('validates the three required fields', async () => {
    const { user, props } = renderForm({
      exercise: { ...exercise, muscleGroupId: '', exerciseType: '', intensity: '' },
    });

    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    expect(screen.getByText('El grupo muscular es obligatorio.')).toBeInTheDocument();
    expect(screen.getByText('El tipo de ejercicio es obligatorio.')).toBeInTheDocument();
    expect(screen.getByText('La intensidad es obligatoria.')).toBeInTheDocument();
    expect(props.onSubmit).not.toHaveBeenCalled();
  });

  it('submits the selected classification values', async () => {
    const { user, props } = renderForm();

    await user.selectOptions(screen.getByLabelText('Grupo muscular'), '2');
    await user.selectOptions(screen.getByLabelText('Tipo de ejercicio'), 'cardio');
    await user.selectOptions(screen.getByLabelText('Intensidad'), 'alto');
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    expect(props.onSubmit).toHaveBeenCalledWith({
      muscleGroupId: '2',
      exerciseType: 'cardio',
      intensity: 'alto',
    });
  });

  it.each([
    [403, 'No tienes permiso para reclasificar este ejercicio.'],
    [409, 'La clasificación duplicada.'],
    [422, 'La clasificación inválida.'],
  ])('shows backend error %s', (status, message) => {
    renderForm({ backendError: Object.assign(new Error(message), { status }) });

    expect(screen.getByRole('alert')).toHaveTextContent(message);
  });

  it('shows the connection error', () => {
    renderForm({
      backendError: Object.assign(new Error('network'), { status: 0 }),
    });

    expect(screen.getByRole('alert')).toHaveTextContent(
      'No se pudo conectar con el servidor.',
    );
  });
});
