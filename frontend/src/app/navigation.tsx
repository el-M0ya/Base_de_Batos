import type { ReactNode } from 'react';
import { Dumbbell, Layers3, MapPin } from 'lucide-react';
import { appRoutes } from './routes';

/** Navigation item displayed in the administration menu. */
export interface AdminNavItem {
  /** Hash route used by the application. */
  href: string;
  /** Visible label. */
  label: string;
  /** Icon displayed beside the label. */
  icon: ReactNode;
}

/** Global links for the administration area. */
export const adminNavigation: readonly AdminNavItem[] = [
  {
    href: `#${appRoutes.exercises}`,
    label: 'Ejercicios',
    icon: <Dumbbell size={18} aria-hidden="true" />,
  },
  { href: '#/admin/sites', label: 'Sitios', icon: <MapPin size={18} aria-hidden="true" /> },
  {
    href: '#/admin/training-programs',
    label: 'Programas de entrenamiento',
    icon: <Dumbbell size={18} aria-hidden="true" />,
  },
  {
    href: '#/admin/muscle-groups',
    label: 'Grupos musculares',
    icon: <Layers3 size={18} aria-hidden="true" />,
  },
];
