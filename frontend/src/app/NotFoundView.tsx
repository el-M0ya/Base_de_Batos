import { messages } from '../shared/i18n/messages';

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
      <h1>{messages.notFound.title}</h1>
      <p>{messages.notFound.description}</p>
    </section>
  );
}
