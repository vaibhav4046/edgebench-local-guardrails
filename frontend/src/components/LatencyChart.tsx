import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  summary: Record<string, unknown> | null;
  records: Array<Record<string, unknown>>;
};

type Row = {
  key: string;
  ttftMean: number;
  ttftP50: number;
  ttftP95: number;
  latencyMean: number;
  latencyP50: number;
  latencyP95: number;
};

function toNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function rowsFromSummary(summary: Record<string, unknown> | null): Row[] {
  const block = (summary?.by_model_temperature as Record<string, Record<string, Record<string, number>>>) || {};
  return Object.entries(block).map(([key, metrics]) => ({
    key,
    ttftMean: metrics?.ttft_seconds?.mean ?? 0,
    ttftP50: metrics?.ttft_seconds?.p50 ?? 0,
    ttftP95: metrics?.ttft_seconds?.p95 ?? 0,
    latencyMean: metrics?.total_response_latency_seconds?.mean ?? 0,
    latencyP50: metrics?.total_response_latency_seconds?.p50 ?? 0,
    latencyP95: metrics?.total_response_latency_seconds?.p95 ?? 0,
  }));
}

function histogram(values: number[], bins = 10): Array<{ bucket: string; count: number }> {
  if (!values.length) {
    return [];
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return [{ bucket: `${min.toFixed(2)}`, count: values.length }];
  }

  const width = (max - min) / bins;
  const counts = new Array<number>(bins).fill(0);
  for (const value of values) {
    const idx = Math.min(bins - 1, Math.floor((value - min) / width));
    counts[idx] += 1;
  }

  return counts.map((count, idx) => {
    const start = min + idx * width;
    const end = idx === bins - 1 ? max : start + width;
    return {
      bucket: `${start.toFixed(2)}-${end.toFixed(2)}`,
      count,
    };
  });
}

function histogramRows(records: Array<Record<string, unknown>>, metricKey: string): Array<{ bucket: string; count: number }> {
  const values: number[] = [];
  for (const record of records) {
    const metrics = record.metrics as Record<string, unknown> | undefined;
    const value = toNumber(metrics?.[metricKey]);
    if (value !== null) {
      values.push(value);
    }
  }
  return histogram(values, 10);
}

export function LatencyChart({ summary, records }: Props) {
  const rows = rowsFromSummary(summary);
  const ttftHistogramRows = histogramRows(records, "ttft_seconds");
  const latencyHistogramRows = histogramRows(records, "total_response_latency_seconds");

  return (
    <section className="panel chart-panel">
      <h2>TTFT + Latency (mean/p50/p95)</h2>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="key" hide />
          <YAxis />
          <Tooltip />
          <Bar dataKey="ttftMean" fill="var(--chart-1)" />
          <Bar dataKey="ttftP50" fill="var(--chart-4)" />
          <Bar dataKey="ttftP95" fill="var(--chart-6)" />
          <Bar dataKey="latencyMean" fill="var(--chart-2)" />
          <Bar dataKey="latencyP50" fill="var(--chart-5)" />
          <Bar dataKey="latencyP95" fill="var(--chart-3)" />
        </BarChart>
      </ResponsiveContainer>

      <h3>TTFT Histogram (sampled records)</h3>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={ttftHistogramRows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bucket" hide />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="var(--chart-1)" />
        </BarChart>
      </ResponsiveContainer>

      <h3>Total Latency Histogram (sampled records)</h3>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={latencyHistogramRows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bucket" hide />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="var(--chart-2)" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
