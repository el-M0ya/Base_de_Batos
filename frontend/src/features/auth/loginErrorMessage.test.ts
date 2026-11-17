import { describe, expect, it } from 'vitest';
import { ApiError } from '../../shared/api/apiError';
import { loginErrorMessage } from './loginErrorMessage';

describe('loginErrorMessage', () => {
  it('distinguishes an inactive account from wrong credentials (both are 401)', () => {
    expect(loginErrorMessage(new ApiError(401, 'The account is inactive.'))).toBe(
      'Tu cuenta está desactivada. Contacta con el administrador.',
    );
    expect(loginErrorMessage(new ApiError(401, 'Invalid email or password.'))).toBe(
      'Correo o contraseña incorrectos. Verifica tus credenciales.',
    );
  });

  it('reports a network error when the server cannot be reached', () => {
    expect(loginErrorMessage(new ApiError(0, 'sin red'))).toBe(
      'No se pudo conectar con el servidor.',
    );
  });

  it('falls back to the generic message for anything else', () => {
    expect(loginErrorMessage(new ApiError(500, 'boom'))).toBe(
      'Error al iniciar sesión. Inténtalo de nuevo.',
    );
    expect(loginErrorMessage(new Error('inesperado'))).toBe(
      'Error al iniciar sesión. Inténtalo de nuevo.',
    );
  });
});
