import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { SitesView } from './SitesView';

const mocks = vi.hoisted(() => ({
  create: vi.fn(),
  update: vi.fn(),
  remove: vi.fn(),
}));

vi.mock('./useSites', () => ({
  useSites: () => ({
    data: [{ id: 'site-1', name: 'Sede Centro', address: 'Calle 10' }],
    error: null,
    isLoading: false,
  }),
  useCreateSite: () => ({ isPending: false, mutateAsync: mocks.create }),
  useUpdateSite: () => ({ isPending: false, mutateAsync: mocks.update }),
  useDeleteSite: () => ({ isPending: false, mutateAsync: mocks.remove }),
}));

describe('SitesView', () => {
  it('loads sites through the query hook and creates a site through the mutation hook', async () => {
    mocks.create.mockResolvedValue({ id: 'site-2', name: 'Sede Norte', address: 'Calle 20' });
    const { user } = renderWithProviders(<SitesView />);

    expect(screen.getByText('Sede Centro')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Nuevo sitio' }));
    await user.type(screen.getByLabelText('Nombre del sitio'), 'Sede Norte');
    await user.type(screen.getByLabelText('Dirección'), 'Calle 20');
    await user.click(screen.getByRole('button', { name: 'Crear sitio' }));

    expect(mocks.create).toHaveBeenCalledWith({ name: 'Sede Norte', address: 'Calle 20' });
  });
});
