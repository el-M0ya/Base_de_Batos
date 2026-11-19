import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { AuthenticatedUser } from '../../shared/types/roles';
import { ExerciseTable } from './ExerciseTable';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
}));

vi.mock('../../shared/auth/useAuth', () => ({
  useAuth: mocks.useAuth,
}));

const exercises = [
  {
    id: 'exercise-1',
    name: 'Press de banca',
    description: 'Trabajo de fuerza.',
    exerciseType: 'fuerza',
    intensity: 'medio',
    muscleGroupId: '1',
    muscleGroupName: 'Pecho',
    trainerId: 'trainer-1',
    registrationDate: '2026-01-15',
  },
  {
    id: 'exercise-2',
    name: 'Remo',
    description: 'Trabajo de espalda.',
    exerciseType: 'fuerza',
    intensity: 'alto',
    muscleGroupId: '2',
    muscleGroupName: 'Espalda',
    trainerId: 'trainer-2',
    registrationDate: '2026-01-16',
  },
];

const trainer = (id: string): AuthenticatedUser => ({
  id,
  email: `${id}@example.com`,
  role: 'trainer',
  capabilities: { can_generate: true, can_validate: false },
});

function renderTable(user: AuthenticatedUser | null = trainer('trainer-1')) {
  mocks.useAuth.mockReturnValue({ user });
  return render(<ExerciseTable exercises={exercises} onReclassify={vi.fn()} />);
}

describe('ExerciseTable', () => {
  it('displays exercise data and all required columns', () => {
    renderTable();

    expect(screen.getByRole('columnheader', { name: /Nombre/ })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Grupo muscular/ })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Tipo/ })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Intensidad/ })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Creador/ })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Fecha de registro/ })).toBeInTheDocument();
    expect(screen.getByText('Press de banca')).toBeInTheDocument();
    expect(screen.getByText('Pecho')).toBeInTheDocument();
    expect(screen.getByText('trainer-1')).toBeInTheDocument();
    expect(screen.getByText('2026-01-15')).toBeInTheDocument();
  });

  it('shows the reclassify action to the creating trainer', () => {
    renderTable(trainer('trainer-1'));

    expect(screen.getByRole('button', { name: 'Editar registro 1' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Editar registro 2' })).not.toBeInTheDocument();
  });

  it.each([
    ['another trainer', trainer('trainer-3')],
    [
      'an administrator',
      {
        ...trainer('trainer-1'),
        role: 'administrator',
      } as AuthenticatedUser,
    ],
    [
      'a client',
      {
        ...trainer('trainer-1'),
        role: 'client',
      } as AuthenticatedUser,
    ],
    ['an unauthenticated user', null],
  ])('hides the reclassify action for %s', (_description, user) => {
    renderTable(user);

    expect(screen.queryByRole('button', { name: 'Editar registro 1' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Editar registro 2' })).not.toBeInTheDocument();
  });

  it('shows the loading state', () => {
    mocks.useAuth.mockReturnValue({ user: trainer('trainer-1') });
    render(<ExerciseTable exercises={[]} loading onReclassify={vi.fn()} />);

    expect(screen.getByRole('status', { name: 'Cargando' })).toBeInTheDocument();
  });

  it('shows the empty state', () => {
    mocks.useAuth.mockReturnValue({ user: trainer('trainer-1') });
    render(<ExerciseTable exercises={[]} onReclassify={vi.fn()} />);

    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });
});
