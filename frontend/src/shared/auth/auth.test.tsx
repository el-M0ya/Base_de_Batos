/**
 * Pruebas del módulo de autenticación compartido (`shared/auth`).
 *
 * @remarks
 * Cubre cada rol/capacidad, cierre de sesión y restauración de sesión tras
 * recarga. El mock de `authApi` simula una demora de red de 400 ms, por lo
 * que las pruebas esperan a que las promesas se resuelvan.
 */
import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './AuthContext';

/** Componente auxiliar que expone los valores de `useAuth` para probarlos. */
function AuthProbe() {
  const { user, hasRole, hasCapability } = useAuth();
  return (
    <div>
      <span data-testid="user-email">{user ? user.email : 'none'}</span>
      <span data-testid="role">{user ? user.role : 'none'}</span>
      <span data-testid="hasRoleAdministrator">{String(hasRole('administrator'))}</span>
      <span data-testid="hasRoleTrainer">{String(hasRole('trainer'))}</span>
      <span data-testid="hasRoleClient">{String(hasRole('client'))}</span>
      <span data-testid="hasCapCanGenerate">{String(hasCapability('can_generate'))}</span>
      <span data-testid="hasCapCanValidate">{String(hasCapability('can_validate'))}</span>
      <span data-testid="isAuthenticated">{String(user !== null)}</span>
    </div>
  );
}

/** Componente con botón de login para un usuario concreto. */
function LoginButton({
  email,
  password,
  testId,
}: {
  email: string;
  password: string;
  testId: string;
}) {
  const { login } = useAuth();
  return (
    <button data-testid={testId} onClick={() => void login(email, password).catch(() => {})}>
      Entrar
    </button>
  );
}

/** Componente con login y logout. */
function LoginLogout() {
  const { login, logout, user, isAuthenticated } = useAuth();
  return (
    <div>
      <button data-testid="login-btn" onClick={() => login('trainer@forjafit.demo', 'trainer2026')}>
        Entrar
      </button>
      <button data-testid="logout-btn" onClick={logout} disabled={!isAuthenticated}>
        Salir
      </button>
      <span data-testid="auth-state">
        {user ? `${user.email}:${String(isAuthenticated)}` : 'ninguna:false'}
      </span>
    </div>
  );
}

function renderWithAuth(ui: React.ReactNode) {
  return { user: userEvent.setup(), ...render(<AuthProvider>{ui}</AuthProvider>) };
}

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
});

/**
 * Espera a que el estado de autenticación se estabilice tras una acción
 * asíncrona (el mock de authApi tarda 400 ms).
 */
async function waitForAuth() {
  await new Promise((resolve) => setTimeout(resolve, 600));
}

describe('AuthContext - roles y capacidades de los usuarios demo', () => {
  it('jefe de sala: rol trainer con can_validate=true', async () => {
    const { user: u, getByTestId } = renderWithAuth(
      <LoginButton email="chief@forjafit.demo" password="chief2026" testId="login-chief" />,
    );

    await u.click(getByTestId('login-chief'));
    await waitForAuth();

    // Remontar un probe para leer el estado tras el login (sessionStorage persiste).
    const { getByTestId: g } = render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );
    await waitForAuth();

    expect(g('role')).toHaveTextContent('trainer');
    expect(g('hasCapCanValidate')).toHaveTextContent('true');
    expect(g('hasCapCanGenerate')).toHaveTextContent('true');
    expect(g('hasRoleAdministrator')).toHaveTextContent('false');
    expect(g('hasRoleClient')).toHaveTextContent('false');
    expect(g('isAuthenticated')).toHaveTextContent('true');
  });

  it('entrenador: rol trainer con can_generate=true, can_validate=false', async () => {
    const { user: u, getByTestId } = renderWithAuth(
      <LoginButton email="trainer@forjafit.demo" password="trainer2026" testId="login-trainer" />,
    );

    await u.click(getByTestId('login-trainer'));
    await waitForAuth();

    const { getByTestId: g } = render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );
    await waitForAuth();

    expect(g('role')).toHaveTextContent('trainer');
    expect(g('hasCapCanGenerate')).toHaveTextContent('true');
    expect(g('hasCapCanValidate')).toHaveTextContent('false');
    expect(g('hasRoleAdministrator')).toHaveTextContent('false');
    expect(g('hasRoleClient')).toHaveTextContent('false');
    expect(g('isAuthenticated')).toHaveTextContent('true');
  });

  it('administrador: rol administrator, sin capacidades', async () => {
    const { user: u, getByTestId } = renderWithAuth(
      <LoginButton email="admin@forjafit.demo" password="admin2026" testId="login-admin" />,
    );

    await u.click(getByTestId('login-admin'));
    await waitForAuth();

    const { getByTestId: g } = render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );
    await waitForAuth();

    expect(g('role')).toHaveTextContent('administrator');
    expect(g('hasRoleTrainer')).toHaveTextContent('false');
    expect(g('hasRoleClient')).toHaveTextContent('false');
    expect(g('hasCapCanGenerate')).toHaveTextContent('false');
    expect(g('hasCapCanValidate')).toHaveTextContent('false');
    expect(g('isAuthenticated')).toHaveTextContent('true');
  });

  it('cliente: rol client, sin capacidades', async () => {
    const { user: u, getByTestId } = renderWithAuth(
      <LoginButton email="client@forjafit.demo" password="client2026" testId="login-client" />,
    );

    await u.click(getByTestId('login-client'));
    await waitForAuth();

    const { getByTestId: g } = render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );
    await waitForAuth();

    expect(g('role')).toHaveTextContent('client');
    expect(g('hasRoleTrainer')).toHaveTextContent('false');
    expect(g('hasRoleAdministrator')).toHaveTextContent('false');
    expect(g('hasCapCanGenerate')).toHaveTextContent('false');
    expect(g('hasCapCanValidate')).toHaveTextContent('false');
    expect(g('isAuthenticated')).toHaveTextContent('true');
  });
});

describe('AuthContext - login, logout y restauración', () => {
  it('credenciales inválidas no inician sesión ni guardan token', async () => {
    const { user: u, getByTestId } = renderWithAuth(
      <LoginButton email="noexiste@forjafit.demo" password="wrong" testId="login-bad" />,
    );

    await u.click(getByTestId('login-bad'));
    await waitForAuth();

    expect(sessionStorage.getItem('forjafit:token')).toBeNull();
    expect(sessionStorage.getItem('forjafit:user')).toBeNull();
  });

  it('logout limpia memoria y sessionStorage', async () => {
    const { user: u, getByTestId } = renderWithAuth(<LoginLogout />);

    await u.click(getByTestId('login-btn'));
    await waitForAuth();
    expect(getByTestId('auth-state')).toHaveTextContent('trainer@forjafit.demo:true');
    expect(sessionStorage.getItem('forjafit:token')).toBe('demo:trainer@forjafit.demo');

    await u.click(getByTestId('logout-btn'));
    await waitForAuth();
    expect(getByTestId('auth-state')).toHaveTextContent('ninguna:false');
    expect(sessionStorage.getItem('forjafit:token')).toBeNull();
    expect(sessionStorage.getItem('forjafit:user')).toBeNull();
  });

  it('restaura la sesión tras recarga (sessionStorage persiste)', async () => {
    // Iniciar sesión como cliente y guardar en sessionStorage.
    const { user: u, getByTestId: g1 } = renderWithAuth(
      <LoginButton email="client@forjafit.demo" password="client2026" testId="login-client" />,
    );
    await u.click(g1('login-client'));
    await waitForAuth();
    expect(sessionStorage.getItem('forjafit:token')).toBe('demo:client@forjafit.demo');

    // Simular recarga: desmontar y montar un nuevo proveedor con AuthProbe.
    cleanup();
    const { getByTestId: g2 } = render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );
    await waitForAuth();

    expect(g2('user-email')).toHaveTextContent('client@forjafit.demo');
    expect(g2('role')).toHaveTextContent('client');
    expect(g2('isAuthenticated')).toHaveTextContent('true');
  });
});
