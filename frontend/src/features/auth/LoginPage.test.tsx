import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { renderWithProviders, screen, cleanup } from '../../test/test-utils';
import { LoginPage } from './LoginPage';

// The container is tested as a user would use it: typing and clicking.
describe('LoginPage', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    cleanup();
  });

  it('shows validation errors and does not submit when the fields are empty', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(screen.getByLabelText('Correo electrónico')).toHaveAccessibleDescription(
      'Introduce tu correo electrónico.',
    );
    expect(screen.getByLabelText('Contraseña')).toHaveAccessibleDescription(
      'Introduce tu contraseña.',
    );
    // While the session is being restored, the button may be disabled;
    // once loading finishes, it should be enabled.
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeEnabled();
  });

  it('rejects an email with an invalid format', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    // Wait for session restore to complete so the button is enabled.
    await new Promise((resolve) => setTimeout(resolve, 100));

    await user.type(screen.getByLabelText('Correo electrónico'), 'no-es-un-correo');
    await user.type(screen.getByLabelText('Contraseña'), 'x');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(screen.getByLabelText('Correo electrónico')).toHaveAccessibleDescription(
      'El correo no tiene un formato válido.',
    );
  });

  it('shows the credentials error for invalid credentials, and lets the user dismiss it', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await new Promise((resolve) => setTimeout(resolve, 100));

    await user.type(screen.getByLabelText('Correo electrónico'), 'otro@forjafit.demo');
    await user.type(screen.getByLabelText('Contraseña'), 'incorrecta');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(
      await screen.findByText('Correo o contraseña incorrectos. Verifica tus credenciales.'),
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Descartar' }));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('accepts valid demo credentials and starts a session', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await new Promise((resolve) => setTimeout(resolve, 100));

    await user.type(screen.getByLabelText('Correo electrónico'), 'trainer@forjafit.demo');
    await user.type(screen.getByLabelText('Contraseña'), 'trainer2026');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    // Successful login: no error alert, no "invalid credentials" message.
    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(
      screen.queryByText('Correo o contraseña incorrectos. Verifica tus credenciales.'),
    ).not.toBeInTheDocument();
    expect(sessionStorage.getItem('forjafit:token')).toBe('demo:trainer@forjafit.demo');
  });

  it('accepts client demo credentials', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await new Promise((resolve) => setTimeout(resolve, 100));

    await user.type(screen.getByLabelText('Correo electrónico'), 'client@forjafit.demo');
    await user.type(screen.getByLabelText('Contraseña'), 'client2026');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(sessionStorage.getItem('forjafit:token')).toBe('demo:client@forjafit.demo');
  });

  it('accepts administrator demo credentials', async () => {
    const { user } = renderWithProviders(<LoginPage />);

    await new Promise((resolve) => setTimeout(resolve, 100));

    await user.type(screen.getByLabelText('Correo electrónico'), 'admin@forjafit.demo');
    await user.type(screen.getByLabelText('Contraseña'), 'admin2026');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(sessionStorage.getItem('forjafit:token')).toBe('demo:admin@forjafit.demo');
  });
});
