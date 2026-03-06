import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Props = {
  summary: Record<string, unknown> | null;
};

function rowsFromSummary(summary: Record<string, unknown> | null) {
  const block = (summary?.error_type_counts as Record<string, number>) || {};
  return Object.entries(block).map(([name, count]) => ({ name, count }));
}

export function FailureChart({ summary }: Props) {
  const rows = rowsFromSummary(summary);
  return (
    <section className="panel chart-panel">
      <h2>Failure Types</h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="var(--chart-3)" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
