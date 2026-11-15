import { describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../shared/api/apiError';
import { renderWithProviders, screen } from '../../test/test-utils';
import { SiteForm } from './SiteForm';

describe('SiteForm', () => {
  it('validates both required fields before calling the API', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { user } = renderWithProviders(<SiteForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Crear sede' }));

    expect(screen.getByText('El nombre es obligatorio.')).toBeInTheDocument();
    expect(screen.getByText('La dirección es obligatoria.')).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits trimmed site values and displays API errors', async () => {
    const onSubmit = vi
      .fn()
      .mockRejectedValue(new ApiError(409, 'Ya existe una sede con ese nombre.', 'DUPLICATE_NAME'));
    const { user } = renderWithProviders(<SiteForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText('Nombre de la sede'), '  Sede Centro  ');
    await user.type(screen.getByLabelText('Dirección'), '  Calle 10  ');
    await user.click(screen.getByRole('button', { name: 'Crear sede' }));

    expect(onSubmit).toHaveBeenCalledWith({ name: 'Sede Centro', address: 'Calle 10' });
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Ya existe una sede con ese nombre.',
    );
  });
});
