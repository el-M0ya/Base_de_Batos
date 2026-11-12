import { NavLink, Outlet } from 'react-router-dom';
import type { NavLinkRenderProps } from 'react-router-dom';
import { useAuth } from '../shared/auth/useAuth';
import { messages } from '../shared/i18n/messages';
import {
  isMenuEntryVisible,
  menuEntries,
} from './routes';
import styles from './AppLayout.module.css';

/**
 * Clase CSS de un enlace de navegación: activa si la ruta coincide.
 *
 * @param props - Propiedades de renderizado de `NavLink`.
 */
const linkClass = (props: NavLinkRenderProps): string | undefined =>
  props.isActive
    ? `${styles.link} ${styles.linkActive}`
    : styles.link;

/**
 * Diseño de la aplicación: barra lateral de navegación, barra superior y área
 * de contenido donde se renderiza la ruta activa mediante `<Outlet />`.
 *
 * @remarks
 * Se usa como elemento de la ruta padre `/` del enrutador, por lo que todas las
 * rutas protegidas heredan este diseño. La ruta `/login` se declara fuera de
 * este layout, por lo que no muestra la barra lateral.
 *
 * El menú filtra cada entrada con `isMenuEntryVisible` según el rol y las
 * capacidades de la sesión, respetando la regla de que una feature no importa
 * de otra: todo lo compartido (sesión, rutas, i18n) vive en `shared`.
 */
export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className={styles.layout}>
      <nav className={styles.sidebar}>
        <div className={styles.brand}>
          <NavLink to="/" className={linkClass} end>
            {messages.app.name}
          </NavLink>
        </div>
        <ul className={styles.list}>
          {menuEntries
            .filter((entry) =>
              isMenuEntryVisible(
                entry,
                (role) => (user ? user.role === role : false),
                (capability) =>
                  user ? (user.capabilities[capability] === true) : false,
              ),
            )
            .map((entry) => (
              <li key={entry.path} className={styles.item}>
                <NavLink to={entry.path} className={linkClass}>
                  {entry.label}
                </NavLink>
              </li>
            ))}
        </ul>
      </nav>
      <main className={styles.main}>
        <header className={styles.header}>
          <h1>{messages.app.name}</h1>
          <button
            className={styles.logout}
            onClick={() => void logout()}
            title={messages.nav.logout}
          >
            {messages.nav.logout}
          </button>
        </header>
        <section className={styles.content}>
          <Outlet />
        </section>
      </main>
    </div>
  );
}
