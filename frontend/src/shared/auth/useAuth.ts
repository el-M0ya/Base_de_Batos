/**
 * Hook para consumir el contexto de autenticación.
 *
 * @remarks
 * Reexportado desde `AuthContext` para tener un archivo dedicado y claro,
 * como indica el listado de archivos de E3-06.
 *
 * @returns El valor del contexto de autenticación (usuario, token, login, logout, etc.).
 * @throws {Error} si se usa fuera de un `AuthProvider`.
 */
export { useAuth, type AuthContextValue } from './AuthContext';
