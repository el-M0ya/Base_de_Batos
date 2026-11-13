/**
 * Página 404: ruta no encontrada.
 *
 * @remarks
 * Se renderiza cuando el navegador solicita una ruta que no está registrada en
 * el enrutador de la aplicación.
 */
export function NotFoundView() {
  return (
    <section className="not-found">
      <h1>Página no encontrada</h1>
      <p>La ruta solicitada no existe.</p>
    </section>
  );
}
