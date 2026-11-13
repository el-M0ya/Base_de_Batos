/**
 * Tipos de dominio para la administración de usuarios y perfiles (E4-06).
 *
 * @remarks
 * Estos tipos modelan la información que el administrador consulta y gestiona
 * sobre cuentas y perfiles. Se definen aquí, en `shared/types`, para que la
 * feature `users` y cualquier otra feature puedan usarlos sin importarse entre
 * sí, respetando la regla de dependencia de E3-02.
 *
 * La forma de estos tipos se basa en `specs.md` (RF-02, RF-03, RF-04, RF-05)
 * y en el dominio del informe de base de datos (USER, TRAINER, CLIENT). No
 * asume la forma exacta de los endpoints de E4-02: esa correspondencia se
 * resuelve en el adaptador de API (`features/users/api.ts`) cuando E4-02 esté
 * disponible.
 */
export type UserRole = 'administrator' | 'trainer' | 'client';

/**
 * Estado de una cuenta de usuario.
 *
 * @remarks
 * La desactivación es una baja lógica (RNF-11): se conserva el registro para
 * mantener la trazabilidad de rutinas, asignaciones y sesiones.
 */
export type AccountStatus = 'active' | 'inactive';

/**
 * Capacidades de sesión de un usuario.
 *
 * @remarks
 * `can_generate` permite generar rutinas; `can_validate` permite revisarlas.
 * Ambas son por programa y con vigencia, pero en la sesión se guarda el valor
 * derivado del usuario autenticado.
 */
export interface UserCapabilities {
  /** Puede generar rutinas en un programa. */
  can_generate: boolean;
  /** Puede validar (revisar/aprobar/rechazar) rutinas en un programa. */
  can_validate: boolean;
}

/**
 * Perfil de entrenador (RF-04).
 */
export interface TrainerProfile {
  /** Especialidad del entrenador. */
  specialty: string;
}

/**
 * Perfil de cliente (RF-05).
 */
export interface ClientProfile {
  /** Edad del cliente (entero positivo). */
  age: number;
  /** Identificador de la sede a la que pertenece el cliente. */
  idSite: number;
}

/**
 * Cuenta de usuario con su perfil especializado.
 *
 * @remarks
 * El rol determina qué perfil está presente: `trainer` trae `trainerProfile`,
 * `client` trae `clientProfile` y `administrator` no trae perfil especializado.
 */
export interface UserAccount {
  /** Identificador único de la cuenta. */
  id: number;
  /** Correo electrónico único (U-1). */
  email: string;
  /** Rol persistido de la cuenta. */
  role: UserRole;
  /** Estado de la cuenta. */
  status: AccountStatus;
  /** Perfil de entrenador, presente solo cuando el rol es `trainer`. */
  trainerProfile?: TrainerProfile;
  /** Perfil de cliente, presente solo cuando el rol es `client`. */
  clientProfile?: ClientProfile;
}

/**
 * Datos para crear una nueva cuenta de usuario.
 */
export interface CreateUserInput {
  /** Correo electrónico (se normaliza a minúsculas). */
  email: string;
  /** Rol de la cuenta. */
  role: UserRole;
  /** Especialidad del entrenador (solo si el rol es `trainer`). */
  specialty?: string;
  /** Edad del cliente (solo si el rol es `client`). */
  age?: number;
  /** Identificador de la sede del cliente (solo si el rol es `client`). */
  idSite?: number;
  /** Contraseña en texto plano (el backend la almacena con hash). */
  password: string;
}

/**
 * Errores de campo del formulario de usuario.
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
 * Datos editables de una cuenta existente.
 */
export interface UpdateUserInput {
  /** Nuevo estado de la cuenta (`active` o `inactive`). */
  status?: AccountStatus;
  /** Nueva especialidad del entrenador. */
  specialty?: string;
  /** Nueva edad del cliente. */
  age?: number;
  /** Nuevo identificador de la sede del cliente. */
  idSite?: number;
}

/**
 * Error de respuesta de la API de usuarios.
 *
 * @remarks
 * `code` es un código estable que permite al frontend mostrar el mensaje
 * adecuado sin depender del texto del backend (por ejemplo, `duplicateEmail`).
 */
export interface UserApiError {
  /** Código estable del error. */
  code: 'duplicateEmail' | 'notFound' | 'forbidden' | 'invalidInput' | 'server';
  /** Mensaje legible para el usuario, en español. */
  message: string;
  /** Campo al que se refiere el error, si corresponde. */
  field?: string;
}

/**
 * Resultado de una operación de la API de usuarios.
 *
 * @remarks
 * Un resultado es exitoso (`ok`) o fallido (`error`). Nunca ambos.
 */
export type UserApiResult<T> = { ok: true; data: T } | { ok: false; error: UserApiError };
