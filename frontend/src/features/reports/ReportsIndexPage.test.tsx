import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { UserRole } from '../../shared/types/roles';
import { ReportsIndexPage } from './ReportsIndexPage';

const mocks = vi.hoisted(() => ({ useAuth: vi.fn() }));
vi.mock('../../shared/auth/useAuth', () => ({ useAuth: mocks.useAuth }));

function renderPage(role: UserRole) {
  mocks.useAuth.mockReturnValue({ user: { role } });
  return render(
    <MemoryRouter>
      <ReportsIndexPage />
    </MemoryRouter>,
  );
}

const cardTitles = () =>
  screen.queryAllByRole('article').map((card) => within(card).getByRole('heading').textContent);

describe('ReportsIndexPage', () => {
  it('shows the six reports to a trainer, all as coming soon', () => {
    renderPage('trainer');

    expect(screen.getAllByRole('article')).toHaveLength(6);
    expect(screen.getAllByText('Próximamente')).toHaveLength(6);
    expect(screen.queryByRole('link', { name: /ver informe/i })).not.toBeInTheDocument();
    expect(screen.getByText('6 informes para tu perfil')).toBeInTheDocument();
  });

  it('shows a client only the reports allowed for clients', () => {
    renderPage('client');

    expect(cardTitles()).toEqual(['Desempeño de clientes en una rutina']);
    expect(screen.getByText('1 informe para tu perfil')).toBeInTheDocument();
  });

  it('lists the three sections of REP-06', () => {
    renderPage('administrator');

    const sections = screen.getByRole('list', { name: 'Secciones del informe' });
    expect(within(sections).getAllByRole('listitem')).toHaveLength(3);
    expect(sections).toHaveTextContent('Ejercicios con mayor abandono');
  });

  it('filters the cards with the search box and updates the tab counters', async () => {
    const user = userEvent.setup();
    renderPage('trainer');

    await user.type(screen.getByRole('searchbox', { name: 'Buscar informes' }), 'validadas');

    expect(cardTitles()).toEqual(['Rutinas validadas por revisor']);
    expect(screen.getByRole('button', { name: 'Todos (1)' })).toBeInTheDocument();
  });

  it('filters by status tab and explains when nothing matches', async () => {
    const user = userEvent.setup();
    renderPage('trainer');

    const available = screen.getByRole('button', { name: 'Disponibles (0)' });
    await user.click(available);

    expect(available).toHaveAttribute('aria-pressed', 'true');
    expect(screen.queryAllByRole('article')).toHaveLength(0);
    expect(screen.getByText('No hay informes que coincidan')).toBeInTheDocument();
  });
});
