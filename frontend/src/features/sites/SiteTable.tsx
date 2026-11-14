import { DataTable } from '../../shared/components/DataTable/DataTable';
import type { ColumnDef } from '../../shared/components/DataTable/columns';
import { messages } from '../../shared/i18n/messages';
import type { Site } from './types';

const t = messages.sites;

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
    { accessor: 'name', header: t.table.name },
    { accessor: 'address', header: t.table.address },
    {
      accessor: 'registrationDate',
      header: t.table.registered,
      format: (value) =>
        value === undefined
          ? messages.common.emptyValue
          : new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(new Date(String(value))),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={[...data]}
      loading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
      ariaLabel={t.tableLabel}
    />
  );
}
