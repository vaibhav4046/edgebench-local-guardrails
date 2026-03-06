import { useEffect, useMemo, useState } from "react";

import { DatasetUploader } from "../components/DatasetUploader";
import { DeterminismChart } from "../components/DeterminismChart";
import { ExportButtons } from "../components/ExportButtons";
import { FailureChart } from "../components/FailureChart";
import { LatencyChart } from "../components/LatencyChart";
import { LiveLogs } from "../components/LiveLogs";
import { MemoryChart } from "../components/MemoryChart";
import { MetricsCards } from "../components/MetricsCards";
import { ModelSelector } from "../components/ModelSelector";
import { ProgressPanel } from "../components/ProgressPanel";
import { RunControls } from "../components/RunControls";
import { ThroughputChart } from "../components/ThroughputChart";
import { getModelSuggestions } from "../api/client";
import { useRunStore } from "../store/runStore";
import type { ModelOverride } from "../types/api";

const defaultModels: ModelOverride[] = [
  { model_key: "llama3.2-mini", tag: "llama3.2:1b-instruct-q4_K_M", base_url: "http://127.0.0.1:11434", enabled: true },
  { model_key: "54Mini", tag: "54Mini:latest", base_url: "http://127.0.0.1:11434", enabled: true },
  { model_key: "mistral-7b", tag: "mistral:7b-instruct", base_url: "http://127.0.0.1:11434", enabled: true },
];

export function DashboardPage() {
  const {
    runs,
    selectedRunId,
    summary,
    records,
    logs,
    error,
    connected,
    datasetPath,
    setDatasetPath,
    refreshRuns,
    startRun,
    cancelRunById,
    selectRun,
    uploadDatasetFile,
  } = useRunStore();

  const [models, setModels] = useState<ModelOverride[]>(defaultModels);
  const [temperature, setTemperature] = useState(0.2);
  const [topP, setTopP] = useState(0.9);
  const [topK, setTopK] = useState(40);
  const [seed, setSeed] = useState(42);
  const [numPredict, setNumPredict] = useState(256);
  const [repeats, setRepeats] = useState(3);
  const [requestTimeout, setRequestTimeout] = useState(120);
  const [jobTimeout, setJobTimeout] = useState(0);
  const [scorerName, setScorerName] = useState<"exact_json" | "field_level">("exact_json");
  const [deterministic, setDeterministic] = useState(false);
  const [enableSweep, setEnableSweep] = useState(false);
  const [temperaturesCsv, setTemperaturesCsv] = useState("0.0,0.2,0.5,0.8");
  const [suggestionsByModelKey, setSuggestionsByModelKey] = useState<Record<string, string[]>>({});

  useEffect(() => {
    void refreshRuns();
  }, [refreshRuns]);

  useEffect(() => {
    let active = true;
    void getModelSuggestions()
      .then((payload) => {
        if (!active) {
          return;
        }
        const next: Record<string, string[]> = {};
        for (const item of payload.models) {
          next[item.model_key] = item.suggested_tags;
        }
        setSuggestionsByModelKey(next);
      })
      .catch(() => {
        if (active) {
          setSuggestionsByModelKey({});
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const selectedRun = useMemo(
    () => runs.find((item) => item.job_id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );

  const canCancel = !!selectedRun && ["queued", "running"].includes(selectedRun.status);

  const parseTemps = (raw: string) =>
    raw
      .split(",")
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isFinite(item));

  const handleStart = async () => {
    await startRun({
      dataset_path: datasetPath,
      models_config_path: "config/models.yaml",
      benchmark_config_path: "config/benchmark.yaml",
      model_overrides: models,
      sampling_override: {
        temperature,
        top_p: topP,
        top_k: topK,
        seed,
        num_predict: numPredict,
      },
      repeats,
      request_timeout_seconds: requestTimeout,
      job_timeout_seconds: jobTimeout,
      deterministic_mode: deterministic,
      deterministic_config_path: "config/deterministic.yaml",
      enable_temperature_sweep: enableSweep,
      temperatures: parseTemps(temperaturesCsv),
      scorer_name: scorerName,
    });
  };

  const handleCancel = async () => {
    if (selectedRunId) {
      await cancelRunById(selectedRunId);
    }
  };

  return (
    <div className="stack">
      <section className="panel">
        <h2>Run Selection</h2>
        <div className="row">
          <label className="grow">
            Active run
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
              {runs.map((run) => (
                <option key={run.job_id} value={run.job_id}>
                  {run.job_id} - {run.status}
                </option>
              ))}
            </select>
          </label>
          <button className="button button-secondary" onClick={() => void refreshRuns()}>
            Refresh
          </button>
        </div>
        <p className="muted">SSE: {connected ? "connected" : "disconnected"}</p>
      </section>

      <ModelSelector models={models} suggestionsByModelKey={suggestionsByModelKey} onChange={setModels} />

      <DatasetUploader
        datasetPath={datasetPath}
        onDatasetPathChange={setDatasetPath}
        onUpload={uploadDatasetFile}
      />

      <section className="panel">
        <h2>Sampling + Determinism</h2>
        <div className="grid-3">
          <label>
            Temperature
            <input type="number" step="0.1" value={temperature} onChange={(e) => setTemperature(Number(e.target.value))} />
          </label>
          <label>
            top_p
            <input type="number" step="0.05" value={topP} onChange={(e) => setTopP(Number(e.target.value))} />
          </label>
          <label>
            top_k
            <input type="number" value={topK} onChange={(e) => setTopK(Number(e.target.value))} />
          </label>
          <label>
            seed
            <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
          </label>
          <label>
            num_predict
            <input type="number" value={numPredict} onChange={(e) => setNumPredict(Number(e.target.value))} />
          </label>
          <label>
            repeats
            <input type="number" min={1} value={repeats} onChange={(e) => setRepeats(Number(e.target.value))} />
          </label>
          <label>
            request timeout (s)
            <input type="number" min={1} value={requestTimeout} onChange={(e) => setRequestTimeout(Number(e.target.value))} />
          </label>
          <label>
            job timeout (s, 0=off)
            <input type="number" min={0} value={jobTimeout} onChange={(e) => setJobTimeout(Number(e.target.value))} />
          </label>
          <label>
            scorer
            <select value={scorerName} onChange={(e) => setScorerName(e.target.value as "exact_json" | "field_level")}>
              <option value="exact_json">exact_json</option>
              <option value="field_level">field_level</option>
            </select>
          </label>
        </div>
        <div className="row">
          <label>
            <input type="checkbox" checked={deterministic} onChange={(e) => setDeterministic(e.target.checked)} />
            Deterministic mode preset
          </label>
          <label>
            <input type="checkbox" checked={enableSweep} onChange={(e) => setEnableSweep(e.target.checked)} />
            Temperature sweep
          </label>
          <label className="grow">
            Sweep values CSV
            <input value={temperaturesCsv} onChange={(e) => setTemperaturesCsv(e.target.value)} />
          </label>
        </div>
      </section>

      <RunControls onStart={handleStart} onCancel={handleCancel} canCancel={canCancel} />
      <ProgressPanel run={selectedRun} />
      <MetricsCards summary={summary} />
      <LatencyChart summary={summary} records={records} />
      <ThroughputChart summary={summary} records={records} />
      <FailureChart summary={summary} />
      <DeterminismChart summary={summary} />
      <MemoryChart summary={summary} />
      <ExportButtons runId={selectedRunId} />
      <LiveLogs logs={logs} />

      {error ? <p className="error">{error}</p> : null}
    </div>
  );
}
