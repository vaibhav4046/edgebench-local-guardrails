import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Props = {
  summary: Record<string, unknown> | null;
};

function rowsFromSummary(summary: Record<string, unknown> | null) {
  const memory = (summary?.memory_usage as unknown as Record<string, unknown>) || {};
  const byModel =
    (memory.by_model_tag_temp as Record<string, Record<string, number>>) ||
    (memory.by_model_tag as Record<string, Record<string, number>>) ||
    {};
  return Object.entries(byModel).map(([key, values]) => ({
    key,
    runnerPeakMB: ((values?.runner_peak_rss_bytes ?? 0) as number) / (1024 * 1024),
    runnerAvgMB: ((values?.runner_avg_rss_bytes ?? 0) as number) / (1024 * 1024),
    ollamaPeakMB: ((values?.ollama_peak_rss_bytes ?? 0) as number) / (1024 * 1024),
    ollamaAvgMB: ((values?.ollama_avg_rss_bytes ?? 0) as number) / (1024 * 1024),
  }));
}

export function MemoryChart({ summary }: Props) {
  const rows = rowsFromSummary(summary);
  return (
    <section className="panel chart-panel">
      <h2>Memory Peak/Avg (MB)</h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="key" hide />
          <YAxis />
          <Tooltip />
          <Bar dataKey="runnerPeakMB" fill="var(--chart-5)" />
          <Bar dataKey="runnerAvgMB" fill="var(--chart-4)" />
          <Bar dataKey="ollamaPeakMB" fill="var(--chart-6)" />
          <Bar dataKey="ollamaAvgMB" fill="var(--chart-2)" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
