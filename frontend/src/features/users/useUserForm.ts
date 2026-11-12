/**
 * Hook de validación para el formulario de usuario (E4-06).
 *
 * @remarks
 * Contiene las reglas de validación del lado del cliente antes de enviar al
 * backend: correo obligatorio y con formato válido, contraseña obligatoria al
 * crear, edad positiva para clientes, y sede obligatoria para clientes. Los
 * errores del backend (por ejemplo, correo duplicado) se inyectan desde el
 * contenedor mediante `setBackendError`.
 */
import { useState, useCallback } from 'react';
import type {
  CreateUserInput,
  UpdateUserInput,
} from '../../shared/types/users';

/**
 * Errores de campo del formulario.
 */
export interface UserFormFieldErrors {
  email?: string;
  password?: string;
  role?: string;
  specialty?: string;
  age?: string;
  idSite?: string;
}

/**
 * Valor devuelto por `useUserForm`.
 */
export interface UseUserFormReturn {
  /** Errores de campo actuales. */
  fieldErrors: UserFormFieldErrors;
  /** Error de backend (por ejemplo, correo duplicado) o `null`. */
  backendError: string | null;
  /** Establece un error de backend (invocado desde el contenedor). */
  setBackendError: (message: string | null) => void;
  /** Limpia el error de backend. */
  clearBackendError: () => void;
  /** Valida los datos de creación. Devuelve `true` si son válidos. */
  validateCreate: (input: CreateUserInput) => boolean;
  /** Valida los datos de actualización. Devuelve `true` si son válidos. */
  validateUpdate: (input: UpdateUserInput) => boolean;
  /** Limpia todos los errores. */
  clearErrors: () => void;
}

/* ------------------------------------------------------------------ */
/* Constantes de validación                                           */
/* ------------------------------------------------------------------ */

/** Patrón simple de correo: algo@algo.algo. */
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Hook de validación para el formulario de usuario.
 *
 * @returns Estado de errores y funciones de validación.
 */
export function useUserForm(): UseUserFormReturn {
  const [fieldErrors, setFieldErrors] = useState<UserFormFieldErrors>({});
  const [backendError, setBackendError] = useState<string | null>(null);

  const clearBackendError = useCallback(() => {
    setBackendError(null);
  }, []);

  const clearErrors = useCallback(() => {
    setFieldErrors({});
    setBackendError(null);
  }, []);

  /**
   * Valida los datos de creación de una cuenta.
   *
   * @remarks
   * Requiere correo con formato válido, contraseña no vacía, rol válido, y
   * para clientes: edad positiva e identificador de sede.
   */
  const validateCreate = useCallback((input: CreateUserInput): boolean => {
    const errors: UserFormFieldErrors = {};

    const email = input.email.trim();
    if (email === '') {
      errors.email = 'Introduce tu correo electrónico.';
    } else if (!EMAIL_PATTERN.test(email)) {
      errors.email = 'El correo no tiene un formato válido.';
    }

    if (input.password === '') {
      errors.password = 'Introduce una contraseña.';
    }

    if (!['administrator', 'trainer', 'client'].includes(input.role)) {
      errors.role = 'Selecciona un rol válido.';
    }

    if (input.role === 'client') {
      if (!input.age || input.age <= 0) {
        errors.age = 'Introduce una edad válida (mayor que cero).';
      }
      if (!input.idSite || input.idSite <= 0) {
        errors.idSite = 'Selecciona una sede.';
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }, []);

  /**
   * Valida los datos de actualización de una cuenta.
   *
   * @remarks
   * Al menos un campo debe estar presente. Si se incluye edad o sede (cliente),
   * deben ser válidos.
   */
  const validateUpdate = useCallback((input: UpdateUserInput): boolean => {
    const errors: UserFormFieldErrors = {};

    const hasAnyField =
      input.status !== undefined ||
      input.specialty !== undefined ||
      input.age !== undefined ||
      input.idSite !== undefined;

    if (!hasAnyField) {
      errors.role = 'Modifica al menos un campo.';
    }

    if (input.age !== undefined && input.age <= 0) {
      errors.age = 'La edad debe ser mayor que cero.';
    }
    if (input.idSite !== undefined && input.idSite <= 0) {
      errors.idSite = 'Selecciona una sede válida.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }, []);

  return {
    fieldErrors,
    backendError,
    setBackendError,
    clearBackendError,
    validateCreate,
    validateUpdate,
    clearErrors,
  };
}
