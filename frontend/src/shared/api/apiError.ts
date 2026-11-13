/**
 * Typed error returned by the shared HTTP client.
 *
 * @remarks
 * Keeping transport errors in one type lets feature forms show server
 * messages without coupling themselves to `fetch` or a specific backend.
 */
export class ApiError extends Error {
  /** HTTP status code, or `0` when no response was received. */
  readonly status: number;
  /** Optional backend error code. */
  readonly code?: string;
  /** Optional field-level validation details returned by the backend. */
  readonly details?: unknown;

  /**
   * Creates an API error.
   *
   * @param status - HTTP status code, or `0` for network errors.
   * @param message - User-facing or backend-provided message.
   * @param code - Optional machine-readable error code.
   * @param details - Optional validation payload.
   */
  constructor(status: number, message: string, code?: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    if (code !== undefined) this.code = code;
    if (details !== undefined) this.details = details;
  }

  /** Returns whether the request failed before receiving an HTTP response. */
  isNetworkError(): boolean {
    return this.status === 0;
  }

  /** Returns whether the server rejected the submitted data. */
  isValidationError(): boolean {
    return this.status >= 400 && this.status < 500 && this.status !== 401 && this.status !== 404;
  }
}
