/**
 * Contract tests for the authentication API (E4-05).
 *
 * @remarks
 * The real implementation is tested with a fake `fetch` (no backend); the
 * mock is tested directly. Both must honour the same contract.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/apiError';
import { authApiReal, isInactiveAccountError } from './authApi';
import { authApiMock } from './authApi.mock';

/** Builds a fake HTTP response with a JSON body and the given status code. */
function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

/** Replaces `fetch` with a fake function that always returns `response`. */
function mockFetch(response: Response) {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

/** Sample user with the exact shape the backend sends. */
const RAW_CHIEF = {
  id: 7,
  email: 'chief@gym.test',
  role: 'trainer',
  capabilities: { can_generate: true, can_validate: true },
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('authApiReal', () => {
  it('envía las credenciales a /auth/login y traduce la respuesta', async () => {
    const fetchMock = mockFetch(
      jsonResponse(200, {
        access_token: 'jwt-123',
        token_type: 'bearer',
        expires_in: 3600,
        user: RAW_CHIEF,
      }),
    );

    const session = await authApiReal.login('chief@gym.test', 'secreta');

    const [url, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(url.pathname).toMatch(/\/auth\/login$/);
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body as string)).toEqual({
      email: 'chief@gym.test',
      password: 'secreta',
    });
    expect(session).toEqual({
      token: 'jwt-123',
      user: {
        id: '7',
        email: 'chief@gym.test',
        role: 'trainer',
        capabilities: { can_generate: true, can_validate: true },
      },
    });
  });

  it('me envía el token y devuelve el usuario actual', async () => {
    const fetchMock = mockFetch(jsonResponse(200, RAW_CHIEF));

    const user = await authApiReal.me('jwt-123');

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer jwt-123');
    expect(user?.id).toBe('7');
    expect(user?.capabilities.can_validate).toBe(true);
  });

  it('me devuelve null si el backend rechaza el token (401)', async () => {
    mockFetch(jsonResponse(401, { detail: 'The access token is invalid.' }));

    await expect(authApiReal.me('caducado')).resolves.toBeNull();
  });

  it('me relanza los errores que no son 401', async () => {
    mockFetch(jsonResponse(500, { detail: 'boom' }));

    await expect(authApiReal.me('jwt-123')).rejects.toBeInstanceOf(ApiError);
  });

  it('rechaza un rol desconocido enviado por el backend', async () => {
    mockFetch(jsonResponse(200, { ...RAW_CHIEF, role: 'superadmin' }));

    await expect(authApiReal.me('jwt-123')).rejects.toBeInstanceOf(ApiError);
  });
});

describe('authApiMock', () => {
  it('inicia sesión y devuelve un token demo', async () => {
    const session = await authApiMock.login('trainer@forjafit.demo', 'trainer2026');

    expect(session.token).toBe('demo:trainer@forjafit.demo');
    expect(session.user.role).toBe('trainer');
  });

  it('rechaza credenciales incorrectas con 401', async () => {
    const error = await authApiMock.login('trainer@forjafit.demo', 'mala').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(401);
    expect(isInactiveAccountError(error)).toBe(false);
  });

  it('rechaza una cuenta desactivada como lo hace el backend', async () => {
    const error = await authApiMock
      .login('inactive@forjafit.demo', 'inactive2026')
      .catch((e: unknown) => e);

    expect(isInactiveAccountError(error)).toBe(true);
  });

  it('me recupera el usuario de un token demo y rechaza uno desconocido', async () => {
    await expect(authApiMock.me('demo:client@forjafit.demo')).resolves.toMatchObject({
      role: 'client',
    });
    await expect(authApiMock.me('demo:nadie@forjafit.demo')).resolves.toBeNull();
  });
});

describe('isInactiveAccountError', () => {
  it('solo reconoce el 401 de cuenta desactivada', () => {
    expect(isInactiveAccountError(new ApiError(401, 'The account is inactive.'))).toBe(true);
    expect(isInactiveAccountError(new ApiError(401, 'Invalid email or password.'))).toBe(false);
    expect(isInactiveAccountError(new ApiError(403, 'The account is inactive.'))).toBe(false);
    expect(isInactiveAccountError(new Error('The account is inactive.'))).toBe(false);
  });
});
