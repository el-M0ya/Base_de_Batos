/**
 * Tests for the shared HTTP client (E4-05).
 *
 * @remarks
 * `fetch` is replaced by a fake function: the real backend is never called.
 * Covers sending the token, reading FastAPI errors and reporting 401s.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from './apiError';
import { HttpClient } from './httpClient';

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

/** Returns the headers sent in the first `fetch` call. */
function sentHeaders(fetchMock: ReturnType<typeof vi.fn>): Headers {
  const requestInit = fetchMock.mock.calls[0]?.[1] as RequestInit;
  return new Headers(requestInit.headers);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('HttpClient', () => {
  it('envía el token como cabecera Authorization cuando hay sesión', async () => {
    const fetchMock = mockFetch(jsonResponse(200, { ok: true }));
    const client = new HttpClient();
    client.setAuthHandlers({ getToken: () => 'abc123', onUnauthorized: vi.fn() });

    await client.get('/exercises');

    expect(sentHeaders(fetchMock).get('Authorization')).toBe('Bearer abc123');
  });

  it('no envía Authorization si nadie registró la sesión', async () => {
    const fetchMock = mockFetch(jsonResponse(200, { ok: true }));
    const client = new HttpClient();

    await client.get('/exercises');

    expect(sentHeaders(fetchMock).has('Authorization')).toBe(false);
  });

  it('usa el campo detail de FastAPI como mensaje de error', async () => {
    mockFetch(jsonResponse(401, { detail: 'The account is inactive.' }));
    const client = new HttpClient();

    const error = await client.post('/auth/login', {}).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(401);
    expect((error as ApiError).message).toBe('The account is inactive.');
  });

  it('avisa con onUnauthorized cuando el backend rechaza el token', async () => {
    mockFetch(jsonResponse(401, { detail: 'The access token is invalid.' }));
    const onUnauthorized = vi.fn();
    const client = new HttpClient();
    client.setAuthHandlers({ getToken: () => 'token-caducado', onUnauthorized });

    await expect(client.get('/exercises')).rejects.toBeInstanceOf(ApiError);

    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });

  it('no avisa con onUnauthorized si el 401 llega sin token (login fallido)', async () => {
    mockFetch(jsonResponse(401, { detail: 'Invalid email or password.' }));
    const onUnauthorized = vi.fn();
    const client = new HttpClient();
    client.setAuthHandlers({ getToken: () => null, onUnauthorized });

    await expect(client.post('/auth/login', {})).rejects.toBeInstanceOf(ApiError);

    expect(onUnauthorized).not.toHaveBeenCalled();
  });
});
