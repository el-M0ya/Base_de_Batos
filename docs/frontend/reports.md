# Reports and PDF export

How the reporting foundation is organized (E3-09, #71), how to connect a real report once its backend query exists, and the known limitations.

**Status:** all six reports (REP-01 to REP-06) are registered and shown as **Próximamente**. Real queries are delivered by the functional reporting epic. PDF export works today and is used by the exercise list.

## 1. Pieces

| Piece            | File                                                     | Job                                                                                              |
| ---------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Registry         | `features/reports/reportsRegistry.ts`                    | Single source of every report: id, code, title, requirements, roles, status, icon, sections.     |
| Catalog page     | `features/reports/ReportsIndexPage.tsx` (+ `ReportCard`) | `/reports`: cards for the reports the user's role may see, search and status tabs.               |
| Catalog search   | `features/reports/filterReports.ts`                      | Pure filter by text (accent- and case-insensitive; code, RF and section titles too) and status.  |
| Detail container | `features/reports/components/ReportContainer.tsx`        | `/reports/:id`: finds the report, checks the role, loads data (future) and renders `ReportView`. |
| Detail view      | `features/reports/components/ReportView.tsx`             | Presentational skeleton: header, filters slot, export button and the body for each state.        |
| Result block     | `features/reports/components/ReportSectionPanel.tsx`     | One "chart + sortable table" block (RF-43). REP-06 renders three.                                |
| Chart wrapper    | `features/reports/components/ChartPanel.tsx`             | Thin wrapper over Recharts; reports pass `{ label, value }[]` and never import Recharts.         |
| PDF table        | `shared/export/buildPdfTable.ts`                         | Pure: columns + visible rows → plain-text `{ head, body }`, formatted like the screen.           |
| PDF document     | `shared/export/exportToPdf.ts`                           | Draws title, optional subtitle, generation date and table with jsPDF, then downloads it.         |
| Export button    | `shared/components/ExportPdfButton.tsx`                  | Reusable button: busy state, no double clicks, error alert.                                      |
| Shared sorting   | `shared/components/DataTable/sortRows.ts`                | The sort used by `DataTable`; callers reuse it so the PDF keeps the on-screen order.             |

## 2. Report ↔ requirement map

| Report | Requirements          | Title                                  | Roles (assumption)                 |
| ------ | --------------------- | -------------------------------------- | ---------------------------------- |
| REP-01 | RF-35                 | Rutinas generadas por programa         | administrator, trainer             |
| REP-02 | RF-36                 | Ejercicios más utilizados              | administrator, trainer             |
| REP-03 | RF-37                 | Rutinas validadas por revisor          | administrator, trainer             |
| REP-04 | RF-38                 | Desempeño de clientes en una rutina    | administrator, trainer, **client** |
| REP-05 | RF-39                 | Comparación de rutinas entre programas | administrator, trainer             |
| REP-06 | RF-40 + RF-41 + RF-42 | Análisis de rendimiento y abandono     | administrator, trainer             |

REP-06 has three sections (intensity/performance correlation, highest abandonment, adjustments vs. site average) because the original item groups three queries.

> **To confirm with the team:** the requirements do not say which role may see each report. The split above is an assumption: reports about routines, programs and validations are for staff; REP-04 also includes clients because the functional requirements let clients consult their progress reports. Changing it only means editing `roles` in the registry.

## 3. Report states

`ReportView` receives a `state` and shows:

| State          | Shown                                                         |
| -------------- | ------------------------------------------------------------- |
| `coming-soon`  | "Próximamente" (backend query not available yet).             |
| `loading`      | Loading text.                                                 |
| `error`        | Error message with **Reintentar**.                            |
| `empty`        | "No hay datos para los filtros seleccionados".                |
| `insufficient` | "No hay datos suficientes para este análisis" (too few rows). |
| `ready`        | Filters, the export button and the results (`children`).      |

## 4. Connecting a real report

1. Create the data hook in `features/reports/` (TanStack Query, same pattern as the other features), with the report filters as its parameters.
2. In `ReportContainer`, for that report id: keep the filter state, call the hook and map it to a `ReportViewState` (`isLoading` → `loading`, error → `error`, no rows → `empty`, below the minimum sample → `insufficient`, otherwise `ready`).
3. Render the filters in the `filters` slot and one `ReportSectionPanel` per query as `children`. Keep the active sort with `onSortChange`.
4. Pass `getExport` returning `{ title, fileName, subtitle, table }`, where `table = buildPdfTable(columns, sortRows(rows, sort.accessor, sort.direction))` and `subtitle` describes the active filters.
5. Set `status: 'available'` in the registry. The card then links to `/reports/<id>`.
6. Add tests for the hook and for the container states.

## 5. Using the PDF export elsewhere

```tsx
<ExportPdfButton
  disabled={rows.length === 0}
  getExport={() => ({
    title: messages.exercises.title,
    fileName: messages.exercises.pdfFileName,
    table: buildPdfTable(
      columns,
      sortRows(rows, sort.accessor, sort.direction),
    ),
  })}
/>
```

- `getExport` runs **at click time**, so the PDF contains exactly what is on screen (active filters and order).
- Reuse the same `ColumnDef` list as the table, so headers and formatting match. Mark visual-only columns with `exportable: false`.
- The file is named `<fileName>-YYYY-MM-DD.pdf`; the document is landscape, with the FORJA purple table header.
- The exercise list (`features/exercises/ExercisesView.tsx`) is the reference implementation.

## 6. Known limitations

- **The PDF does not include the chart.** The issue makes it optional; only the table, title, subtitle and generation date are exported. The same data is always in the table.
- **One table per export.** `exportToPdf` draws one table. REP-06 will need either one export per section or an extension that accepts several tables.
- **Lazy loading.** jsPDF and its table plugin are loaded with `import()` only when the user exports (verified in the build: they are separate chunks). Recharts is also lazy-loaded through `ChartPanel`, but no screen uses a chart yet, so its separate chunk will appear in the build with the first real report.
- **Standard PDF font.** jsPDF's built-in Helvetica covers Spanish characters (accents, ñ, —, …), which was checked with a generated file; characters outside Latin-1 would need an embedded font.
