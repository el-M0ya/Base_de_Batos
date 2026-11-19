import { messages } from '../shared/i18n/messages';

/**
 * Vista de inicio (dashboard) de la aplicación.
 *
 * @remarks
 * Página de aterrizaje tras iniciar sesión. Muestra un resumen breve y los
 * accesos rápidos disponibles según el rol y capacidades de la sesión. Es la
 * ruta raíz (`/`) del application shell.
 */
export function DashboardView() {
  return (
    <section className="dashboard">
      <h1>{messages.dashboard.title}</h1>
      <p>{messages.dashboard.welcome}</p>
    </section>
  );
}
