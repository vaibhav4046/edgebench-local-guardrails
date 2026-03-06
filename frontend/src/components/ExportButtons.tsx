import { exportCsvUrl, exportJsonUrl } from "../api/client";

type Props = {
  runId: string | null;
};

export function ExportButtons({ runId }: Props) {
  if (!runId) {
    return null;
  }

  return (
    <section className="panel">
      <h2>Export</h2>
      <div className="row">
        <a className="button button-secondary" href={exportCsvUrl(runId)} target="_blank" rel="noreferrer">
          Export CSV
        </a>
        <a className="button button-secondary" href={exportJsonUrl(runId)} target="_blank" rel="noreferrer">
          Export JSON
        </a>
      </div>
    </section>
  );
}
