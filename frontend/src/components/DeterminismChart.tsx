import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Props = {
  summary: Record<string, unknown> | null;
};

function rowsFromSummary(summary: Record<string, unknown> | null) {
  const block = (summary?.determinism as Record<string, Record<string, Record<string, number>>>) || {};
  const byGroup = (block.by_model_temperature as Record<string, { exact_match_rate: number }>) || {};
  return Object.entries(byGroup).map(([key, payload]) => ({
    key,
    rate: (payload?.exact_match_rate ?? 0) * 100,
  }));
}

export function DeterminismChart({ summary }: Props) {
  const rows = rowsFromSummary(summary);
  return (
    <section className="panel chart-panel">
      <h2>Determinism Exact-Match (%)</h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="key" hide />
          <YAxis />
          <Tooltip />
          <Bar dataKey="rate" fill="var(--chart-4)" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
