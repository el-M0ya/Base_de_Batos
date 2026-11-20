import type { ColumnDef } from '../../shared/components/DataTable/columns';
import { messages } from '../../shared/i18n/messages';
import type { Exercise } from './types';

const t = messages.exercises;

/**
 * Columns of the exercise list. Shared by the table on screen and the PDF
 * export, so both show the same headers and formatting.
 */
export const exerciseColumns: ColumnDef<Exercise>[] = [
  { accessor: 'name', header: messages.common.columns.name },
  { accessor: 'muscleGroupName', header: t.table.muscleGroup },
  { accessor: 'exerciseType', header: t.table.type },
  { accessor: 'intensity', header: t.table.intensity },
  { accessor: 'trainerId', header: t.table.creator },
  {
    accessor: 'registrationDate',
    header: t.table.registrationDate,
    format: (value) => value ?? messages.common.emptyValue,
  },
];
