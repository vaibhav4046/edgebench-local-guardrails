import { useEffect, useState } from "react";

import { useRunStore } from "../store/runStore";

export function RunDetailPage() {
  const { selectedRunId, summary, records, resultRuns, refreshResultRuns, selectRun } = useRunStore();
  const [manualRunId, setManualRunId] = useState("");

  useEffect(() => {
    void refreshResultRuns();
  }, [refreshResultRuns]);

  return (
    <div className="stack">
      <section className="panel">
        <h2>Run Detail / Results Viewer</h2>
        <p className="muted">Load any local run folder under `results/&lt;run_id&gt;`.</p>

        <div className="row">
          <label className="grow">
            Select discovered run
            <select
              value={selectedRunId ?? ""}
              onChange={(e) => {
                const value = e.target.value;
                if (value) {
                  void selectRun(value);
                }
              }}
            >
              <option value="">Select run...</option>
              {resultRuns.map((item) => (
                <option key={item.run_id} value={item.run_id}>
                  {item.run_id}
                </option>
              ))}
            </select>
          </label>
          <button className="button button-secondary" onClick={() => void refreshResultRuns()}>
            Refresh folders
          </button>
        </div>

        <div className="row">
          <label className="grow">
            Or open run id manually
            <input
              value={manualRunId}
              onChange={(e) => setManualRunId(e.target.value)}
              placeholder="e.g. job_ab12cd34ef56"
            />
          </label>
          <button
            className="button"
            onClick={() => {
              if (manualRunId.trim()) {
                void selectRun(manualRunId.trim());
              }
            }}
          >
            Open
          </button>
        </div>

        <p className="muted">Active run: {selectedRunId ?? "none"}</p>
      </section>

      <section className="panel">
        <h2>Summary JSON</h2>
        <pre className="logbox">{JSON.stringify(summary, null, 2)}</pre>
      </section>

      <section className="panel">
        <h2>Sample Records (first 50)</h2>
        <pre className="logbox">{JSON.stringify(records.slice(0, 50), null, 2)}</pre>
      </section>
    </div>
  );
}
