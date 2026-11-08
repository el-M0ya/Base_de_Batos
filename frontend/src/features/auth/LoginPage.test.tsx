import { describe, expect, it } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { LoginPage } from './LoginPage';

// The container is tested as a user would use it: typing and clicking.
describe('LoginPage', () => {
  it('shows validation errors and does not submit when the fields are empty', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(screen.getByLabelText('Correo electrónico')).toHaveAccessibleDescription(
      'Introduce tu correo electrónico.',
    );
    expect(screen.getByLabelText('Contraseña')).toHaveAccessibleDescription(
      'Introduce tu contraseña.',
    );
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeEnabled();
  });

  it('rejects an email with an invalid format', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText('Correo electrónico'), 'no-es-un-correo');
    await user.type(screen.getByLabelText('Contraseña'), 'x');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(screen.getByLabelText('Correo electrónico')).toHaveAccessibleDescription(
      'El correo no tiene un formato válido.',
    );
  });

  it('shows the credentials error, and lets the user dismiss it', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText('Correo electrónico'), 'otro@forjafit.cu');
    await user.type(screen.getByLabelText('Contraseña'), 'incorrecta');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(
      await screen.findByText('Correo o contraseña incorrectos. Verifica tus credenciales.'),
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Descartar' }));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('accepts the demo credentials', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText('Correo electrónico'), 'demo@forjafit.cu');
    await user.type(screen.getByLabelText('Contraseña'), 'forja2026');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByRole('status')).toHaveTextContent('Credenciales correctas');
  });
});
