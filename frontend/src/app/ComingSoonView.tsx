import { messages } from '../shared/i18n/messages';

/**
 * Vista temporal "Próximamente" para las secciones que aún no se implementan.
 *
 * @remarks
 * Se usa en E3-05 como elemento de las rutas de funcionalidades que llegarán
 * en épicas posteriores (ejercicios, rutinas, informes, administración). Cuando
 * cada feature se construya, su ruta apuntará al componente real.
 *
 * @param section - Nombre de la sección que se mostrará como "próximamente".
 */
export function ComingSoonView({ section }: { section: string }) {
  return (
    <section className="coming-soon">
      <h1>{messages.comingSoon.heading(section)}</h1>
      <p>{messages.comingSoon.description}</p>
    </section>
  );
}
