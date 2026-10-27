/**
 * Typed error thrown by the HTTP client for any non-successful response.
 */
export class ApiError extends Error {
  /** HTTP status code, or 0 for network/unknown failures. */
  readonly status: number;
  /** Optional machine-readable error code returned by the backend. */
  readonly code?: string;
  /** Optional validation details returned by the backend. */
  readonly details?: unknown;

  /**
   * Creates an API error.
   *
   * @param status - HTTP status code.
   * @param message - Human readable message.
   * @param code - Optional error code.
   * @param details - Optional validation details.
   */
  constructor(status: number, message: string, code?: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    if (code !== undefined) this.code = code;
    if (details !== undefined) this.details = details;
  }

  /**
   * Whether the error represents a network failure.
   *
   * @returns `true` when no HTTP response was received.
   */
  isNetworkError(): boolean {
    return this.status === 0;
  }

  /**
   * Whether the error is a validation error (HTTP 4xx except 401/403/404).
   *
   * @returns `true` when the status is in the 400-499 range.
   */
  isValidationError(): boolean {
    return this.status >= 400 && this.status < 500 && this.status !== 401 && this.status !== 403 && this.status !== 404;
  }
}