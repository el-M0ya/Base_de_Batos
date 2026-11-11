import { DataTable } from '../../shared/components/DataTable/DataTable';
import type { ColumnDef } from '../../shared/components/DataTable/columns';
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
 * This wrapper adapts the feature model to the official shared DataTable.
 */
export function SiteTable({ data, isLoading = false, onEdit, onDelete }: SiteTableProps) {
  const columns: ColumnDef<Site>[] = [
    { accessor: 'name', header: 'Nombre' },
    { accessor: 'address', header: 'Dirección' },
    {
      accessor: 'registrationDate',
      header: 'Registrado',
      format: (value) =>
        value === undefined
          ? '—'
          : new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(
              new Date(String(value)),
            ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={[...data]}
      loading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
      ariaLabel="Catálogo de sitios de gimnasios"
    />
  );
}
