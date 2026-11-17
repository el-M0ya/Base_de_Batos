import { lazy, Suspense, useId } from 'react';
import { messages } from '../../../shared/i18n/messages';
import styles from './ChartPanel.module.css';

/** The Recharts chart, loaded only when a panel is rendered. */
const BarChartCanvas = lazy(() => import('./BarChartCanvas'));

/** One bar of the chart. */
export interface ChartDatum {
  /** Category shown on the horizontal axis, e.g. a muscle group. */
  label: string;
  /** Measured value. */
  value: number;
}

/** Props of the chart panel. */
export interface ChartPanelProps {
  /** Chart title; it also names the single series. */
  title: string;
  /** Data to draw. */
  data: ChartDatum[];
  /** Name of the measured value, shown in the tooltip (e.g. "Veces utilizado"). */
  valueLabel: string;
}

/**
 * Thin wrapper over the charting library (Recharts) for the reports.
 *
 * @remarks
 * Reports pass plain `{ label, value }` data and never import Recharts
 * directly, so the library could be replaced in one place. The same data is
 * always shown in the report table, which is the accessible alternative.
 */
export function ChartPanel({ title, data, valueLabel }: ChartPanelProps) {
  const titleId = useId();
  return (
    <figure className={styles.panel} aria-labelledby={titleId}>
      <figcaption id={titleId} className={styles.title}>
        {title}
      </figcaption>
      <Suspense fallback={<p className={styles.loading}>{messages.reports.detail.chartLoading}</p>}>
        <BarChartCanvas data={data} valueLabel={valueLabel} />
      </Suspense>
    </figure>
  );
}
