import { describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../shared/api/apiError';
import { renderWithProviders, screen } from '../../test/test-utils';
import { MuscleGroupForm } from './MuscleGroupForm';

function renderForm(onSubmit = vi.fn().mockResolvedValue(undefined)) {
  return {
    onSubmit,
    ...renderWithProviders(<MuscleGroupForm onSubmit={onSubmit} onCancel={vi.fn()} />),
  };
}

describe('MuscleGroupForm', () => {
  it('requires the group name and does not submit invalid data', async () => {
    const { onSubmit, user } = renderForm();

    await user.click(screen.getByRole('button', { name: 'Crear grupo' }));

    expect(screen.getByText('El nombre es obligatorio.')).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('shows the server duplicate-name error', async () => {
    const onSubmit = vi
      .fn()
      .mockRejectedValue(new ApiError(409, 'Ya existe un grupo muscular con ese nombre.', 'DUPLICATE_NAME'));
    const { user } = renderForm(onSubmit);

    await user.type(screen.getByLabelText('Nombre'), 'Pecho');
    await user.click(screen.getByRole('button', { name: 'Crear grupo' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Ya existe un grupo muscular con ese nombre.',
    );
  });
});
