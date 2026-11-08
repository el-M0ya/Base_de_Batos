import { messages } from './shared/i18n/messages';

/**
 * Componente raíz de la aplicación.
 *
 * @remarks
 * Por ahora solo muestra el nombre del sistema. En E3-05 se sustituye por el
 * enrutador con el layout y la navegación por rol.
 */
export function App() {
  return (
    <main>
      <h1>{messages.app.name}</h1>
      <p>{messages.app.tagline}</p>
    </main>
  );
}
