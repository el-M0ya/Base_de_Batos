import { describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { TextField } from './TextField';

describe('TextField', () => {
  it('links the label to the input', () => {
    renderWithProviders(<TextField label="Correo electrónico" type="email" />);

    // Finding the input by its label only works if they are linked.
    expect(screen.getByLabelText('Correo electrónico')).toHaveAttribute('type', 'email');
  });

  it('lets the user type', async () => {
    const { user } = renderWithProviders(<TextField label="Correo electrónico" />);

    const input = screen.getByLabelText('Correo electrónico');
    await user.type(input, 'atleta@forjafit.cu');

    expect(input).toHaveValue('atleta@forjafit.cu');
  });

  it('shows the error, marks the input as invalid and links the message', () => {
    renderWithProviders(<TextField label="Correo electrónico" error="Correo no válido" />);

    const input = screen.getByLabelText('Correo electrónico');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('alert')).toHaveTextContent('Correo no válido');
    expect(input).toHaveAccessibleDescription('Correo no válido');
  });

  it('shows the hint when there is no error', () => {
    renderWithProviders(<TextField label="Nombre" hint="Como aparecerá en tu perfil" />);

    expect(screen.getByLabelText('Nombre')).toHaveAccessibleDescription(
      'Como aparecerá en tu perfil',
    );
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('toggles the password visibility', async () => {
    const { user } = renderWithProviders(<TextField label="Contraseña" type="password" />);

    const input = screen.getByLabelText('Contraseña');
    expect(input).toHaveAttribute('type', 'password');

    await user.click(screen.getByRole('button', { name: 'Mostrar contraseña' }));
    expect(input).toHaveAttribute('type', 'text');

    await user.click(screen.getByRole('button', { name: 'Ocultar contraseña' }));
    expect(input).toHaveAttribute('type', 'password');
  });

  it('does not show the toggle for non-password fields', () => {
    renderWithProviders(<TextField label="Correo electrónico" type="email" />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
