type Props = {
  summary: Record<string, unknown> | null;
};

function pct(value: unknown): string {
  if (typeof value !== "number") {
    return "-";
  }
  return `${(value * 100).toFixed(2)}%`;
}

export function MetricsCards({ summary }: Props) {
  return (
    <section className="card-grid">
      <article className="metric-card">
        <h3>Schema Pass Rate</h3>
        <p>{pct(summary?.schema_pass_rate)}</p>
      </article>
      <article className="metric-card">
        <h3>Retry Rate</h3>
        <p>{pct(summary?.retry_rate)}</p>
      </article>
      <article className="metric-card">
        <h3>Failure Rate</h3>
        <p>{pct(summary?.failure_rate)}</p>
      </article>
      <article className="metric-card">
        <h3>Total Records</h3>
        <p>{String(summary?.total_records ?? "-")}</p>
      </article>
    </section>
  );
}
