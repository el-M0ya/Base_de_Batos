import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from './apiError';
import { httpClient } from './httpClient';

describe('HttpClient', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('returns parsed JSON on success', async () => {
    const payload = { id: '1', name: 'Press' };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await httpClient.get<{ id: string; name: string }>('/exercises');

    expect(result).toEqual(payload);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('throws ApiError on validation error', async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ message: 'Datos inválidos', code: 'VALIDATION' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(httpClient.post('/exercises', {})).rejects.toBeInstanceOf(ApiError);
    try {
      await httpClient.post('/exercises', {});
    } catch (error) {
      const apiError = error as ApiError;
      expect(apiError.status).toBe(400);
      expect(apiError.message).toBe('Datos inválidos');
      expect(apiError.code).toBe('VALIDATION');
    }
  });

  it('throws ApiError with status 0 on network failure', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'));
    vi.stubGlobal('fetch', fetchMock);

    await expect(httpClient.get('/exercises')).rejects.toBeInstanceOf(ApiError);
    try {
      await httpClient.get('/exercises');
    } catch (error) {
      const apiError = error as ApiError;
      expect(apiError.status).toBe(0);
      expect(apiError.isNetworkError()).toBe(true);
    }
  });
});