import type { ReactNode } from 'react';
import { Menu, X } from 'lucide-react';
import { useState } from 'react';
import { adminNavigation } from '../navigation';
import styles from './AdminLayout.module.css';

/** Props for the global administration layout. */
export interface AdminLayoutProps {
  /** Current hash route, used to mark the active navigation item. */
  currentPath: string;
  /** Content rendered below the navigation header. */
  children: ReactNode;
}

/**
 * Shared shell for administration pages.
 *
 * @remarks
 * Route-specific pages stay inside `features/*`; this component owns only
 * global navigation and layout concerns, as required by the app layer rules.
 */
export function AdminLayout({ currentPath, children }: AdminLayoutProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  /** Closes the mobile menu after selecting a route. */
  function closeMenu() {
    setIsMenuOpen(false);
  }

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <a className={styles.brand} href="#/admin/sites" onClick={closeMenu}>
          Base de Batos
          <span className={styles.brandDot} aria-hidden="true" />
        </a>
        <button
          type="button"
          className={styles.menuButton}
          aria-expanded={isMenuOpen}
          aria-controls="admin-navigation"
          aria-label={isMenuOpen ? 'Cerrar menú' : 'Abrir menú'}
          onClick={() => setIsMenuOpen((open) => !open)}
        >
          {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      <div className={styles.body}>
        <nav
          id="admin-navigation"
          className={`${styles.navigation} ${isMenuOpen ? styles.navigationOpen : ''}`}
          aria-label="Administración"
        >
          <p className={styles.navigationTitle}>Administración</p>
          {adminNavigation.map((item) => {
            const itemPath = item.href.slice(1);
            const isActive = currentPath === itemPath;
            return (
              <a
                key={item.href}
                className={`${styles.link} ${isActive ? styles.active : ''}`}
                href={item.href}
                aria-current={isActive ? 'page' : undefined}
                onClick={closeMenu}
              >
                {item.icon}
                <span>{item.label}</span>
              </a>
            );
          })}
        </nav>

        <div className={styles.content}>{children}</div>
      </div>
    </div>
  );
}
