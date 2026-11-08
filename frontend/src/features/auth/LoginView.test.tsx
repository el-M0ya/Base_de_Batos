import { describe, expect, it, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/test-utils';
import { LoginView, type LoginViewProps } from './LoginView';

// The view is tested with props only: no state, no server.
function renderView(overrides: Partial<LoginViewProps> = {}) {
  const props: LoginViewProps = {
    email: '',
    password: '',
    fieldErrors: {},
    formError: null,
    successMessage: null,
    isSubmitting: false,
    onEmailChange: vi.fn(),
    onPasswordChange: vi.fn(),
    onSubmit: vi.fn(),
    onDismissMessage: vi.fn(),
    ...overrides,
  };
  return { props, ...renderWithProviders(<LoginView {...props} />) };
}

describe('LoginView', () => {
  it('renders the title, both fields and the submit button', () => {
    renderView();

    expect(screen.getByRole('heading', { name: 'Inicia sesión' })).toBeInTheDocument();
    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument();
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeInTheDocument();
  });

  it('reports typing through the callbacks', async () => {
    const { props, user } = renderView();

    await user.type(screen.getByLabelText('Correo electrónico'), 'a');
    await user.type(screen.getByLabelText('Contraseña'), 'b');

    expect(props.onEmailChange).toHaveBeenCalledWith('a');
    expect(props.onPasswordChange).toHaveBeenCalledWith('b');
  });

  it('calls onSubmit when the form is sent', async () => {
    const { props, user } = renderView();

    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(props.onSubmit).toHaveBeenCalledTimes(1);
  });

  it('shows field errors and the general error it receives', () => {
    renderView({
      fieldErrors: { email: 'Introduce tu correo electrónico.' },
      formError: 'Correo o contraseña incorrectos.',
    });

    expect(screen.getByLabelText('Correo electrónico')).toHaveAccessibleDescription(
      'Introduce tu correo electrónico.',
    );
    expect(screen.getByText('Correo o contraseña incorrectos.')).toBeInTheDocument();
  });

  it('disables the button while submitting', () => {
    renderView({ isSubmitting: true });

    expect(screen.getByRole('button', { name: 'Entrar' })).toBeDisabled();
  });
});
