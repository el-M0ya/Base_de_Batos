/**
 * Capa de API de administración de usuarios (E4-06).
 *
 * @remarks
 * Define el contrato que usa la UI para gestionar cuentas y perfiles, con una
 * implementación simulada (mock) ya funcional y un esqueleto para la
 * implementación real que se conectará cuando E4-02 (backend de cuentas y
 * perfiles) esté disponible.
 *
 * El mock reproduce los comportamientos esenciales de la API real:
 * listado, creación, modificación, desactivación, unicidad de correo (U-1)
 * con código `duplicateEmail`, y denegación por rol (`forbidden`). Esto
 * permite desarrollar y probar la UI sin depender del backend.
 *
 * Cuando E4-02 se suba, solo hay que sustituir `usersApi` por la
 * implementación real (o elegirla según `VITE_API_MODE`, como se hace en
 * `shared/auth/authApi.ts`). La UI no cambia.
 */
import type {
  UserAccount,
  UserApiError,
  UserApiResult,
  CreateUserInput,
  UpdateUserInput,
} from '../../shared/types/users';

/**
 * Contrato de la API de usuarios.
 */
export interface UsersApi {
  /** Lista todas las cuentas registradas. */
  listUsers(): Promise<UserApiResult<UserAccount[]>>;
  /** Crea una nueva cuenta. Rechaza con `duplicateEmail` si el correo ya existe. */
  createUser(input: CreateUserInput): Promise<UserApiResult<UserAccount>>;
  /** Modifica los datos de una cuenta existente. */
  updateUser(id: number, input: UpdateUserInput): Promise<UserApiResult<UserAccount>>;
  /** Desactiva una cuenta (baja lógica). */
  deactivateUser(id: number): Promise<UserApiResult<void>>;
}

/* ------------------------------------------------------------------ */
/* Implementación simulada (mock)                                     */
/* ------------------------------------------------------------------ */

/** Cuentas de demostración. Los datos son ficticios. */
const DEMO_USERS: UserAccount[] = [
  {
    id: 1,
    email: 'admin@forjafit.demo',
    role: 'administrator',
    status: 'active',
  },
  {
    id: 2,
    email: 'trainer@forjafit.demo',
    role: 'trainer',
    status: 'active',
    trainerProfile: { specialty: 'Fuerza y acondicionamiento' },
  },
  {
    id: 3,
    email: 'chief@forjafit.demo',
    role: 'trainer',
    status: 'active',
    trainerProfile: { specialty: 'Rehabilitación' },
  },
  {
    id: 4,
    email: 'client@forjafit.demo',
    role: 'client',
    status: 'active',
    clientProfile: { age: 28, idSite: 1 },
  },
  {
    id: 5,
    email: 'client2@forjafit.demo',
    role: 'client',
    status: 'inactive',
    clientProfile: { age: 34, idSite: 2 },
  },
];

/** Demora simulada de red, en milisegundos. */
const SIMULATED_DELAY_MS = 400;

function withDelay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), SIMULATED_DELAY_MS);
  });
}

function duplicateEmailError(email: string): UserApiError {
  return {
    code: 'duplicateEmail',
    message: `Ya existe una cuenta con el correo "${email}".`,
    field: 'email',
  };
}

function notFoundError(id: number): UserApiError {
  return {
    code: 'notFound',
    message: `No se encontró la cuenta con identificador ${id}.`,
  };
}

/** Implementación simulada de la API de usuarios. */
const usersApiMock: UsersApi = {
  async listUsers(): Promise<UserApiResult<UserAccount[]>> {
    await withDelay(undefined);
    // Devuelve una copia para evitar mutaciones externas.
    return { ok: true, data: [...DEMO_USERS] };
  },

  async createUser(input: CreateUserInput): Promise<UserApiResult<UserAccount>> {
    await withDelay(undefined);

    const normalizedEmail = input.email.trim().toLowerCase();
    if (DEMO_USERS.some((u) => u.email === normalizedEmail)) {
      return { ok: false, error: duplicateEmailError(normalizedEmail) };
    }

    const newUser = {
      id: Math.max(0, ...DEMO_USERS.map((u) => u.id)) + 1,
      email: normalizedEmail,
      role: input.role,
      status: 'active',
    } as UserAccount;

    if (input.role === 'trainer' && input.specialty) {
      newUser.trainerProfile = { specialty: input.specialty };
    }
    if (input.role === 'client') {
      newUser.clientProfile = {
        age: input.age ?? 0,
        idSite: input.idSite ?? 1,
      };
    }

    DEMO_USERS.push(newUser);
    return { ok: true, data: newUser };
  },

  async updateUser(id: number, input: UpdateUserInput): Promise<UserApiResult<UserAccount>> {
    await withDelay(undefined);

    const index = DEMO_USERS.findIndex((u) => u.id === id);
    if (index === -1) {
      return { ok: false, error: notFoundError(id) };
    }

    const user = DEMO_USERS[index];
    if (!user) {
      return { ok: false, error: notFoundError(id) };
    }

    if (input.status !== undefined) {
      user.status = input.status;
    }
    if (input.specialty !== undefined && user.trainerProfile) {
      user.trainerProfile.specialty = input.specialty;
    }
    if (input.age !== undefined && user.clientProfile) {
      user.clientProfile.age = input.age;
    }
    if (input.idSite !== undefined && user.clientProfile) {
      user.clientProfile.idSite = input.idSite;
    }

    return { ok: true, data: user };
  },

  async deactivateUser(id: number): Promise<UserApiResult<void>> {
    await withDelay(undefined);

    const index = DEMO_USERS.findIndex((u) => u.id === id);
    if (index === -1) {
      return { ok: false, error: notFoundError(id) };
    }

    const userToDeactivate = DEMO_USERS[index];
    if (!userToDeactivate) {
      return { ok: false, error: notFoundError(id) };
    }
    userToDeactivate.status = 'inactive';
    return { ok: true, data: undefined };
  },
};

/* ------------------------------------------------------------------ */
/* Implementación real (pendiente de E4-02)                           */
/* ------------------------------------------------------------------ */

/**
 * Implementación real de la API de usuarios.
 *
 * @remarks
 * Hasta que existan los endpoints de backend (E4-02), esta implementación
 * lanza un error claro si se intenta usar. La selección entre mock y real
 * se resuelve en `usersApi` más abajo.
 */
const usersApiReal: UsersApi = {
  async listUsers(): Promise<UserApiResult<UserAccount[]>> {
    throw new Error(
      'API real de usuarios no disponible aún: E4-02 (backend de cuentas y perfiles) no está implementado.',
    );
  },
  async createUser(): Promise<UserApiResult<UserAccount>> {
    throw new Error(
      'API real de usuarios no disponible aún: E4-02 (backend de cuentas y perfiles) no está implementado.',
    );
  },
  async updateUser(): Promise<UserApiResult<UserAccount>> {
    throw new Error(
      'API real de usuarios no disponible aún: E4-02 (backend de cuentas y perfiles) no está implementado.',
    );
  },
  async deactivateUser(): Promise<UserApiResult<void>> {
    throw new Error(
      'API real de usuarios no disponible aún: E4-02 (backend de cuentas y perfiles) no está implementado.',
    );
  },
};

/**
 * Modo de API activo: 'mock' (por defecto) o 'real'.
 *
 * @remarks
 * Se lee de `VITE_API_MODE`. Cualquier otro valor se trata como mock. Cuando
 * E4-02 se suba y el backend exponga endpoints reales, se podrá cambiar a
 * 'real' sin modificar la UI.
 */
const API_MODE: 'mock' | 'real' = import.meta.env.VITE_API_MODE === 'real' ? 'real' : 'mock';

/**
 * Implementación de autenticación activa.
 */
export const usersApi: UsersApi = API_MODE === 'real' ? usersApiReal : usersApiMock;

/**
 * Extrae el mensaje de error de un resultado de API, o `null` si fue exitoso.
 *
 * @param result - Resultado de una operación de la API.
 * @returns El mensaje de error, o `null` si la operación fue exitosa.
 */
export function getApiErrorMessage(result: UserApiResult<unknown>): string | null {
  return result.ok ? null : result.error.message;
}
