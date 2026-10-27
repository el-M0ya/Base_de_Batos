import { getApiBaseUrl } from './apiMode';
import { ApiError } from './apiError';
import { getAuthToken } from '../utils/tokenStorage';

/**
 * Options accepted by every HTTP request.
 */
export interface RequestOptions {
  /** Optional query parameters appended to the URL. */
  params?: Record<string, string | number | boolean | undefined>;
  /** Optional request body serialized as JSON. */
  body?: unknown;
  /** Optional extra headers. */
  headers?: HeadersInit;
  /** Optional abort signal. */
  signal?: AbortSignal;
}

/**
 * Builds a URL with optional query parameters.
 *
 * @param path - The API path.
 * @param params - Optional query parameters.
 * @returns The full URL string.
 */
function buildUrl(path: string, params?: RequestOptions['params']): string {
  const base = getApiBaseUrl().replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${base}${normalizedPath}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

/**
 * Typed HTTP client wrapping `fetch`.
 */
export class HttpClient {
  /**
   * Performs a request and returns the parsed JSON body.
   *
   * @param method - HTTP method.
   * @param path - API path.
   * @param options - Request options.
   * @returns The parsed response body.
   * @throws {ApiError} When the response is not successful or the network fails.
   */
  async request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
    const url = buildUrl(path, options.params);
    const headers = new Headers(options.headers);
    if (options.body !== undefined) {
      headers.set('Content-Type', 'application/json');
    }
    const token = getAuthToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    let response: Response;
    try {
      const init: RequestInit = { method, headers };
      if (options.body !== undefined) {
        init.body = JSON.stringify(options.body);
      }
      if (options.signal) {
        init.signal = options.signal;
      }
      response = await fetch(url, init);
    } catch {
      throw new ApiError(0, 'No se pudo conectar con el servidor.');
    }

    if (!response.ok) {
      let message = response.statusText || 'Error de la API';
      let code: string | undefined;
      let details: unknown;
      try {
        const data = (await response.json()) as { message?: string; code?: string; details?: unknown };
        if (data.message) message = data.message;
        code = data.code;
        details = data.details;
      } catch {
        // Response body is not JSON; keep status text.
      }
      throw new ApiError(response.status, message, code, details);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const text = await response.text();
    if (text === '') {
      return undefined as T;
    }
    return JSON.parse(text) as T;
  }

  /**
   * Performs a GET request.
   *
   * @param path - API path.
   * @param options - Request options.
   * @returns The parsed response body.
   */
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', path, options);
  }

  /**
   * Performs a POST request.
   *
   * @param path - API path.
   * @param body - Request body.
   * @param options - Request options.
   * @returns The parsed response body.
   */
  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, { ...options, body });
  }

  /**
   * Performs a PUT request.
   *
   * @param path - API path.
   * @param body - Request body.
   * @param options - Request options.
   * @returns The parsed response body.
   */
  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', path, { ...options, body });
  }

  /**
   * Performs a PATCH request.
   *
   * @param path - API path.
   * @param body - Request body.
   * @param options - Request options.
   * @returns The parsed response body.
   */
  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PATCH', path, { ...options, body });
  }

  /**
   * Performs a DELETE request.
   *
   * @param path - API path.
   * @param options - Request options.
   * @returns The parsed response body.
   */
  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, options);
  }
}

/**
 * Shared HTTP client instance.
 */
export const httpClient = new HttpClient();