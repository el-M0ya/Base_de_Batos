import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { UserRole } from '../../../shared/types/roles';
import { ReportContainer } from './ReportContainer';

const mocks = vi.hoisted(() => ({ useAuth: vi.fn() }));
vi.mock('../../../shared/auth/useAuth', () => ({ useAuth: mocks.useAuth }));

function renderAt(path: string, role: UserRole) {
  mocks.useAuth.mockReturnValue({ user: { role } });
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/reports/:id" element={<ReportContainer />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ReportContainer', () => {
  it('shows the report header and "coming soon" for an allowed role', () => {
    renderAt('/reports/rep-03', 'trainer');

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Rutinas validadas por revisor',
    );
    expect(screen.getByText('Próximamente')).toBeInTheDocument();
  });

  it('blocks a role the report does not allow', () => {
    renderAt('/reports/rep-03', 'client');

    expect(screen.getByRole('alert')).toHaveTextContent(
      'No tienes permiso para acceder a esta página.',
    );
    expect(screen.queryByRole('heading', { level: 1 })).not.toBeInTheDocument();
  });

  it('lets a client open the report allowed for clients', () => {
    renderAt('/reports/rep-04', 'client');

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Desempeño de clientes en una rutina',
    );
  });

  it('explains when the report does not exist', () => {
    renderAt('/reports/rep-99', 'administrator');

    expect(screen.getByText('Informe no encontrado')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Volver a informes' })).toBeInTheDocument();
  });
});
