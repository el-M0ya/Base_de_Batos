import { describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { findReport, type ReportDefinition } from '../reportsRegistry';
import { ReportSectionPanel } from './ReportSectionPanel';
import { ReportView, type ReportViewState } from './ReportView';

// The chart is drawn by Recharts, which needs a real layout; a stub is enough here.
vi.mock('./BarChartCanvas', () => ({
  default: () => <div data-testid="bar-chart" />,
}));

function getReport(id: string): ReportDefinition {
  const report = findReport(id);
  if (report === undefined) throw new Error(`Unknown report ${id}`);
  return report;
}

const rep02 = getReport('rep-02');

interface Row {
  name: string;
  uses: number;
}

const section = (
  <ReportSectionPanel<Row>
    columns={[
      { accessor: 'name', header: 'Ejercicio' },
      { accessor: 'uses', header: 'Veces utilizado' },
    ]}
    rows={[{ name: 'Sentadilla', uses: 12 }]}
    tableLabel="Ranking de frecuencia"
    chart={{ title: 'Uso por ejercicio', valueLabel: 'Veces utilizado', data: [] }}
  />
);

interface RenderOptions {
  report?: ReportDefinition;
  children?: ReactNode;
  onRetry?: () => void;
}

function renderView(state: ReportViewState, options: RenderOptions = {}) {
  return render(
    <MemoryRouter>
      <ReportView
        report={options.report ?? rep02}
        state={state}
        filters={<label>Programa</label>}
        getExport={() => ({ title: 'x', fileName: 'x', table: { head: [], body: [] } })}
        onRetry={options.onRetry ?? (() => {})}
      >
        {options.children ?? section}
      </ReportView>
    </MemoryRouter>,
  );
}

describe('ReportView', () => {
  it('shows the report header with its code and requirements', () => {
    renderView('coming-soon');

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Ejercicios más utilizados',
    );
    expect(screen.getByText('REP-02')).toBeInTheDocument();
    expect(screen.getByText('RF-36')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Volver a informes' })).toHaveAttribute(
      'href',
      '/reports',
    );
  });

  it('shows "coming soon" without filters, results or export', () => {
    renderView('coming-soon');

    expect(screen.getByText('Próximamente')).toBeInTheDocument();
    expect(screen.queryByText('Programa')).not.toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Exportar PDF' })).not.toBeInTheDocument();
  });

  it('shows the loading state', () => {
    renderView('loading');

    expect(screen.getByText('Cargando…')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('shows the error state with a retry button', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    renderView('error', { onRetry });

    await user.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('explains when the filters return no data', () => {
    renderView('empty');

    expect(screen.getByText('No hay datos para los filtros seleccionados')).toBeInTheDocument();
    expect(screen.getByText('Programa')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Exportar PDF' })).not.toBeInTheDocument();
  });

  it('explains when there is not enough data for the analysis', () => {
    renderView('insufficient');

    expect(screen.getByText('No hay datos suficientes para este análisis')).toBeInTheDocument();
  });

  it('shows filters, chart, table and the export button when ready', async () => {
    renderView('ready');

    expect(screen.getByText('Programa')).toBeInTheDocument();
    expect(screen.getByRole('table', { name: 'Ranking de frecuencia' })).toHaveTextContent(
      'Sentadilla',
    );
    expect(screen.getByText('Uso por ejercicio')).toBeInTheDocument();
    expect(await screen.findByTestId('bar-chart')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Exportar PDF' })).toBeEnabled();
  });

  it('renders one block per section for REP-06', () => {
    const rep06 = getReport('rep-06');
    renderView('ready', {
      report: rep06,
      children: rep06.sections?.map((item) => (
        <ReportSectionPanel<Row>
          key={item.requirement}
          title={item.title}
          requirement={item.requirement}
          columns={[{ accessor: 'name', header: 'Ejercicio' }]}
          rows={[{ name: 'Sentadilla', uses: 1 }]}
          tableLabel={item.title}
        />
      )),
    });

    const headings = screen.getAllByRole('heading', { level: 2 });
    expect(headings.map((heading) => heading.textContent)).toEqual([
      'Correlación intensidad-rendimientoRF-40',
      'Ejercicios con mayor abandonoRF-41',
      'Ajustes frente al promedio de la sedeRF-42',
    ]);
    expect(screen.getAllByRole('table')).toHaveLength(3);
  });
});
