import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { MuscleGroupTable } from './MuscleGroupTable';

const groups = [
  {
    id: 'group-1',
    name: 'Pecho',
    description: 'Músculos pectorales.',
    createdAt: '2026-01-01T00:00:00.000Z',
  },
];

describe('MuscleGroupTable', () => {
  it('renders catalog data and row actions', () => {
    renderWithProviders(
      <MuscleGroupTable data={groups} onEdit={vi.fn()} onDelete={vi.fn()} />,
    );

    expect(screen.getByRole('table', { name: 'Catálogo de grupos musculares' })).toBeInTheDocument();
    expect(screen.getByText('Pecho')).toBeInTheDocument();
    expect(screen.getByText('Músculos pectorales.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Editar registro 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Eliminar registro 1' })).toBeInTheDocument();
  });
});
