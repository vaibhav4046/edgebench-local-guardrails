import type { RunJob } from "../types/api";

type Props = {
  run: RunJob | null;
};

export function ProgressPanel({ run }: Props) {
  const current = run?.progress_current ?? 0;
  const total = run?.progress_total ?? 0;
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <section className="panel">
      <h2>Progress</h2>
      <div className="progress-wrap">
        <div className="progress-bar" style={{ width: `${pct}%` }} />
      </div>
      <p className="muted">
        {run ? `${run.status.toUpperCase()} - ${current}/${total} (${pct}%)` : "No run selected"}
      </p>
    </section>
  );
}
