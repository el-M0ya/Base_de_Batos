import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { TrainingProgramForm } from './TrainingProgramForm';

const groups = [
  { id: 'group-1', name: 'Pecho', description: '' },
  { id: 'group-2', name: 'Espalda', description: '' },
];

describe('TrainingProgramForm', () => {
  it('allows selecting multiple muscle groups and submits their identifiers', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { user } = renderWithProviders(
      <TrainingProgramForm
        muscleGroups={groups}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );

    await user.type(screen.getByLabelText('Nombre del programa'), 'Fuerza');
    await user.type(screen.getByLabelText('Objetivo'), 'Ganar fuerza');
    await user.click(screen.getByLabelText('Pecho'));
    await user.click(screen.getByLabelText('Espalda'));
    await user.click(screen.getByRole('button', { name: 'Crear programa' }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: 'Fuerza',
      objective: 'Ganar fuerza',
      muscleGroupIds: ['group-1', 'group-2'],
    });
    expect(screen.getByText('Pecho, Espalda')).toBeInTheDocument();
  });

  it('requires name, objective and at least one muscle group', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { user } = renderWithProviders(
      <TrainingProgramForm muscleGroups={groups} onSubmit={onSubmit} onCancel={vi.fn()} />,
    );

    await user.click(screen.getByRole('button', { name: 'Crear programa' }));

    expect(screen.getByText('El nombre es obligatorio.')).toBeInTheDocument();
    expect(screen.getByText('El objetivo es obligatorio.')).toBeInTheDocument();
    expect(screen.getByText('Selecciona al menos un grupo muscular.')).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
