import { useState } from 'react';
import { messages } from '../../shared/i18n/messages';
import { LoginView, type LoginFieldErrors } from './LoginView';

const t = messages.login;

// Simple shape check: something@something.something
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * TEMPORARY fake login, so the screen can be tried without a backend.
 * TODO(E3-06): replace with `authApi` (mock/real) and the session context.
 */
const DEMO_CREDENTIALS = { email: 'demo@forjafit.cu', password: 'forja2026' };
const FAKE_DELAY_MS = 600;

function fakeLogin(email: string, password: string): Promise<boolean> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(email === DEMO_CREDENTIALS.email && password === DEMO_CREDENTIALS.password);
    }, FAKE_DELAY_MS);
  });
}

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
 */
export function LoginPage() {
  // --- State: everything that can change on this screen ---
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<LoginFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    setFormError(null);
    setSuccessMessage(null);

    const errors = validate(email, password);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return; // invalid fields: do not call the server
    }

    setIsSubmitting(true);
    const isValid = await fakeLogin(email.trim(), password);
    setIsSubmitting(false);

    if (isValid) {
      setSuccessMessage(t.demoSuccess);
    } else {
      setFormError(t.errors.invalidCredentials);
    }
  }

  function dismissMessage() {
    setFormError(null);
    setSuccessMessage(null);
  }

  return (
    <LoginView
      email={email}
      password={password}
      fieldErrors={fieldErrors}
      formError={formError}
      successMessage={successMessage}
      isSubmitting={isSubmitting}
      onEmailChange={setEmail}
      onPasswordChange={setPassword}
      onSubmit={() => void handleSubmit()}
      onDismissMessage={dismissMessage}
    />
  );
}
