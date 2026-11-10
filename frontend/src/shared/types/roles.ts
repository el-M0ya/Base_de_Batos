/**
 * Roles persistidos y capacidades de sesión del usuario.
 *
 * @remarks
 * El informe persiste tres roles en `USER.rol`: administrador, entrenador y cliente.
 * El jefe de sala no es un rol persistido: es un entrenador con `can_validate = true`.
 * Las capacidades se derivan de `AUTHORISES` (puedeGenerar, puedeValidar) por programa.
 */
export type UserRole = 'administrator' | 'trainer' | 'client';

/**
 * Capacidades del usuario en la sesión actual.
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
 * Usuario autenticado, con rol y capacidades.
 */
export interface AuthenticatedUser {
  /** Identificador único del usuario. */
  id: string;
  /** Correo electrónico usado para iniciar sesión. */
  email: string;
  /** Rol persistido del usuario. */
  role: UserRole;
  /** Capacidades activas de la sesión. */
  capabilities: UserCapabilities;
}
