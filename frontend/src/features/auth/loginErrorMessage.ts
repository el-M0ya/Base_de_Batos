import { ApiError } from '../../shared/api/apiError';
import { isInactiveAccountError } from '../../shared/auth/authApi';
import { messages } from '../../shared/i18n/messages';

const t = messages.login;

/**
 * Chooses the message shown when a login attempt fails.
 *
 * @remarks
 * Order matters: an inactive account is also a 401, so it is checked before
 * the generic wrong-credentials case.
 *
 * @param error - Whatever the login call threw.
 * @returns A user-facing Spanish message.
 */
export function loginErrorMessage(error: unknown): string {
  if (isInactiveAccountError(error)) return t.errors.accountInactive;
  if (error instanceof ApiError && error.status === 401) return t.errors.invalidCredentials;
  if (error instanceof ApiError && error.isNetworkError()) return messages.common.networkError;
  return t.sessionError;
}
