import { ApiError } from './apiError';
import { messages } from '../i18n/messages';

/** Options shared by all HTTP requests. */
export interface RequestOptions {
  /** Query parameters appended to the request URL. */
  params?: Record<string, string | number | boolean | undefined>;
  /** JSON body sent with the request. */
  body?: unknown;
  /** Additional request headers. */
  headers?: HeadersInit;
  /** Signal used to cancel a request. */
  signal?: AbortSignal;
}

/**
 * Small typed wrapper around the browser Fetch API.
 *
 * @remarks
 * Feature API modules depend on this abstraction rather than calling
 * `fetch` directly, which makes the real implementation easy to replace in
 * tests or adapt when the backend contract changes.
 */
export class HttpClient {
  /**
   * Executes a request and parses its JSON response.
   *
   * @param method - HTTP method.
   * @param path - Relative API path.
   * @param options - Request options.
   * @returns Parsed response body.
   * @throws {@link ApiError} When the network or server request fails.
   */
  async request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
    const url = new URL(`${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`);

    for (const [key, value] of Object.entries(options.params ?? {})) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }

    const headers = new Headers(options.headers);
    headers.set('Accept', 'application/json');
    if (options.body !== undefined) headers.set('Content-Type', 'application/json');

    const requestInit: RequestInit = { method, headers };
    if (options.body !== undefined) requestInit.body = JSON.stringify(options.body);
    if (options.signal !== undefined) requestInit.signal = options.signal;

    let response: Response;
    try {
      response = await fetch(url, requestInit);
    } catch {
      throw new ApiError(0, messages.common.networkError);
    }

    if (!response.ok) {
      let message = response.statusText || messages.common.requestFailed;
      let code: string | undefined;
      let details: unknown;

      try {
        const payload = (await response.json()) as {
          message?: string;
          code?: string;
          details?: unknown;
        };
        if (payload.message !== undefined) message = payload.message;
        code = payload.code;
        details = payload.details;
      } catch {
        // A non-JSON response still produces a useful ApiError from its status.
      }

      throw new ApiError(response.status, message, code, details);
    }

    if (response.status === 204) return undefined as T;

    const text = await response.text();
    return text === '' ? (undefined as T) : (JSON.parse(text) as T);
  }

  /** Executes a GET request. */
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', path, options);
  }

  /** Executes a POST request. */
  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, { ...options, body });
  }

  /** Executes a PUT request. */
  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', path, { ...options, body });
  }

  /** Executes a DELETE request. */
  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, options);
  }
}

/** Shared real-API HTTP client instance. */
export const httpClient = new HttpClient();
