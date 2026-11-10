import { DataTable, type DataTableColumn } from '../../shared/components/DataTable';
import type { Site } from './types';

/** Props for the gym-site table. */
export interface SiteTableProps {
  /** Records to display. */
  data: readonly Site[];
  /** Whether the catalog request is in progress. */
  isLoading?: boolean;
  /** Opens the edit form for a site. */
  onEdit: (site: Site) => void;
  /** Starts the delete flow for a site. */
  onDelete: (site: Site) => void;
}

/**
 * Catalog table for gym sites.
 *
 * @remarks
 * This wrapper is the feature boundary around the temporary shared
 * DataTable, so adopting the official E3-04 table will not affect the page.
 */
export function SiteTable({ data, isLoading = false, onEdit, onDelete }: SiteTableProps) {
  const columns: readonly DataTableColumn<Site>[] = [
    { key: 'name', header: 'Nombre' },
    { key: 'address', header: 'Dirección' },
    {
      key: 'registrationDate',
      header: 'Registrado',
      render: (site) =>
        site.registrationDate === undefined
          ? '—'
          : new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(
              new Date(site.registrationDate),
            ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      getRowKey={(site) => site.id}
      onEdit={onEdit}
      onDelete={onDelete}
      emptyMessage="No hay sitios registrados."
      ariaLabel="Catálogo de sitios de gimnasios"
    />
  );
}
