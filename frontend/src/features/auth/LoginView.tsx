import type { FormEvent } from 'react';
import { ArrowLeft, ArrowRight, Lock, Mail } from 'lucide-react';
import { Alert } from '../../shared/components/Alert';
import { Button } from '../../shared/components/Button';
import { TextField } from '../../shared/components/TextField';
import { messages } from '../../shared/i18n/messages';
import styles from './LoginView.module.css';

const t = messages.login;

/** Validation errors per field. A missing key means the field is valid. */
export interface LoginFieldErrors {
  /** Error of the email field. */
  email?: string;
  /** Error of the password field. */
  password?: string;
}

/** Everything the login view needs. It receives data and reports events; it holds no state. */
export interface LoginViewProps {
  /** Current value of the email field. */
  email: string;
  /** Current value of the password field. */
  password: string;
  /** Validation errors shown below each field. */
  fieldErrors: LoginFieldErrors;
  /** General error shown in the alert box (e.g. wrong credentials). */
  formError: string | null;
  /** Success message shown in the alert box. */
  successMessage: string | null;
  /** True while the login request is in progress. */
  isSubmitting: boolean;
  /** Called on every change of the email field. */
  onEmailChange: (value: string) => void;
  /** Called on every change of the password field. */
  onPasswordChange: (value: string) => void;
  /** Called when the form is submitted. */
  onSubmit: () => void;
  /** Called when the user closes the alert box. */
  onDismissMessage: () => void;
}

/**
 * Presentational login screen
 *
 * @remarks
 * Pure view: it only draws what it receives through props and calls the
 * `on*` callbacks. The logic lives in `LoginPage`.
 */
export function LoginView({
  email,
  password,
  fieldErrors,
  formError,
  successMessage,
  isSubmitting,
  onEmailChange,
  onPasswordChange,
  onSubmit,
  onDismissMessage,
}: LoginViewProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    // Without this, the browser would reload the page when submitting the form.
    event.preventDefault();
    onSubmit();
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <span className={styles.brand}>
          {t.brand}
          <span className={styles.brandDot} aria-hidden="true" />
        </span>
        {/* TODO(E3-05): turn into a router link to the landing page. */}
        <a className={styles.backLink} href="#">
          <ArrowLeft size={16} aria-hidden="true" />
          {t.backToHome}
        </a>
      </header>

      <main className={styles.main}>
        <section className={styles.card} aria-labelledby="login-title">
          <div className={styles.titleRow}>
            <span className={styles.logoBox} aria-hidden="true">
              <BrandMark />
            </span>
            <h1 id="login-title" className={styles.title}>
              {t.title}
            </h1>
          </div>

          {formError !== null && (
            <Alert variant="error" onDismiss={onDismissMessage}>
              {formError}
            </Alert>
          )}
          {successMessage !== null && (
            <Alert variant="success" onDismiss={onDismissMessage}>
              {successMessage}
            </Alert>
          )}

          <form className={styles.form} onSubmit={handleSubmit} noValidate>
            <TextField
              label={t.emailLabel}
              type="email"
              autoComplete="email"
              placeholder={t.emailPlaceholder}
              icon={<Mail />}
              value={email}
              onChange={(event) => onEmailChange(event.target.value)}
              error={fieldErrors.email}
            />
            <TextField
              label={t.passwordLabel}
              type="password"
              autoComplete="current-password"
              placeholder={t.passwordPlaceholder}
              icon={<Lock />}
              value={password}
              onChange={(event) => onPasswordChange(event.target.value)}
              error={fieldErrors.password}
            />

            <div className={styles.forgotRow}>
              {/* TODO: password recovery is not in the requirements yet. */}
              <a href="#">{t.forgotPassword}</a>
            </div>

            <Button
              type="submit"
              fullWidth
              isLoading={isSubmitting}
              icon={<ArrowRight size={18} />}
            >
              {t.submit}
            </Button>
          </form>

          <footer className={styles.cardFooter}>
            {t.noAccount} {/* TODO(E3-05): router link to the sign-up page. */}
            <a href="#">{t.createAccount}</a>
          </footer>
        </section>
      </main>
    </div>
  );
}

/** Dumbbell + bolt mark from the login model. */
function BrandMark() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
      <path d="M4 7H6V17H4V7Z" fill="currentColor" opacity="0.8" />
      <path d="M2 9H4V15H2V9Z" fill="currentColor" opacity="0.5" />
      <path d="M18 7H20V17H18V7Z" fill="currentColor" opacity="0.8" />
      <path d="M20 9H22V15H20V9Z" fill="currentColor" opacity="0.5" />
      <path d="M6 11.5H18V12.5H6V11.5Z" fill="currentColor" />
      <path d="M13.5 3L8 13H12.5L10.5 21L17.5 10H12.5L13.5 3Z" fill="var(--color-primary)" />
    </svg>
  );
}
