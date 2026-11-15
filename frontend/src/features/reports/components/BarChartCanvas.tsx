/**
 * Recharts bar chart used by `ChartPanel`.
 *
 * @remarks
 * Kept in its own file so `ChartPanel` can load it lazily: Recharts is only
 * downloaded when a report actually shows a chart. Single series, so there is
 * no legend (the panel title names it); thin bars with rounded data ends,
 * recessive grid and axes, and a tooltip on hover.
 */
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { ChartDatum } from './ChartPanel';

/** Props of the bar chart. */
export interface BarChartCanvasProps {
  /** One bar per item. */
  data: ChartDatum[];
  /** Name of the measured value, shown in the tooltip. */
  valueLabel: string;
}

// FORJA tokens (CSS variables work in SVG attributes, so dark theme colors apply).
const BAR = 'var(--color-primary)';
const GRID = 'var(--color-border)';
const AXIS_TEXT = 'var(--color-text-muted)';

/** Draws the bars. Default export so `React.lazy` can load it. */
export default function BarChartCanvas({ data, valueLabel }: BarChartCanvasProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis
          dataKey="label"
          tick={{ fill: AXIS_TEXT, fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: GRID }}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: AXIS_TEXT, fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip
          cursor={{ fill: 'var(--color-surface-raised)' }}
          contentStyle={{
            background: 'var(--color-surface-raised)',
            border: '1px solid var(--color-border-input)',
            borderRadius: 12,
            color: 'var(--color-text)',
          }}
          labelStyle={{ color: 'var(--color-text)' }}
          itemStyle={{ color: 'var(--color-text)' }}
        />
        <Bar
          dataKey="value"
          name={valueLabel}
          fill={BAR}
          radius={[4, 4, 0, 0]}
          maxBarSize={40}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
