import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChartPanel } from './ChartPanel';

const canvas = vi.hoisted(() => vi.fn());
vi.mock('./BarChartCanvas', () => ({
  default: (props: unknown) => {
    canvas(props);
    return <div data-testid="bar-chart" />;
  },
}));

describe('ChartPanel', () => {
  it('shows the title and passes the plain data to the chart', async () => {
    const data = [
      { label: 'Pecho', value: 12 },
      { label: 'Piernas', value: 8 },
    ];
    render(<ChartPanel title="Uso por grupo muscular" valueLabel="Veces utilizado" data={data} />);

    expect(screen.getByRole('figure', { name: 'Uso por grupo muscular' })).toBeInTheDocument();
    expect(await screen.findByTestId('bar-chart')).toBeInTheDocument();
    expect(canvas).toHaveBeenCalledWith({ data, valueLabel: 'Veces utilizado' });
  });
});
