import { useState } from 'react';
import { useAuth } from '../../shared/auth/useAuth';
import { messages } from '../../shared/i18n/messages';
import { LoginView, type LoginFieldErrors } from './LoginView';

const t = messages.login;

// Simple shape check: something@something.something
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Checks the fields on the client before calling the server. */
function validate(email: string, password: string): LoginFieldErrors {
  const errors: LoginFieldErrors = {};
  if (email.trim() === '') {
    errors.email = t.errors.emailRequired;
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = t.errors.emailInvalid;
  }
  if (password === '') {
    errors.password = t.errors.passwordRequired;
  }
  return errors;
}

/**
 * Login screen container: holds the form state and the login logic,
 * and renders `LoginView` with it.
 *
 * @remarks
 * Delegates the actual authentication to `useAuth` (backed by `authApi`),
 * so it works with the mock implementation until backend endpoints exist.
 */
export function LoginPage() {
  const { login, isLoading } = useAuth();

  // --- State: everything that can change on this screen ---
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<LoginFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    setFormError(null);

    const errors = validate(email, password);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return; // invalid fields: do not call the server
    }

    setIsSubmitting(true);
    try {
      await login(email.trim(), password);
    } catch (error: unknown) {
      setIsSubmitting(false);
      const err = error as { status?: number; message?: string };
      if (err.status === 401) {
        setFormError(t.errors.invalidCredentials);
      } else {
        setFormError(t.sessionError);
      }
      return;
    }
    setIsSubmitting(false);
  }

  function dismissMessage() {
    setFormError(null);
  }

  return (
    <LoginView
      email={email}
      password={password}
      fieldErrors={fieldErrors}
      formError={formError}
      successMessage={null}
      isSubmitting={isSubmitting || isLoading}
      onEmailChange={setEmail}
      onPasswordChange={setPassword}
      onSubmit={() => void handleSubmit()}
      onDismissMessage={dismissMessage}
    />
  );
}
