export type ModelOverride = {
  model_key: string;
  tag: string;
  base_url: string;
  enabled: boolean;
};

export type SamplingOverride = {
  temperature: number;
  top_p: number;
  top_k: number;
  seed?: number;
  num_predict?: number;
};

export type RunJob = {
  job_id: string;
  status: string;
  progress_current: number;
  progress_total: number;
  result_dir?: string | null;
  error_message?: string | null;
  cancel_requested: boolean;
  created_at_utc: string;
  updated_at_utc: string;
  payload: Record<string, unknown>;
};

export type RunEvent = Record<string, unknown>;

export type RunRequest = {
  dataset_path: string;
  models_config_path: string;
  benchmark_config_path: string;
  model_overrides?: ModelOverride[];
  sampling_override?: SamplingOverride;
  results_root?: string;
  repeats?: number;
  request_timeout_seconds?: number;
  job_timeout_seconds?: number;
  deterministic_mode?: boolean;
  deterministic_config_path?: string;
  enable_temperature_sweep?: boolean;
  temperatures?: number[];
  scorer_name?: "exact_json" | "field_level";
};

export type SummaryResponse = Record<string, unknown>;

export type RecordResponse = {
  ok: boolean;
  items: Array<Record<string, unknown>>;
  offset: number;
  limit: number;
};

export type ResultRunInfo = {
  run_id: string;
  summary_exists: boolean;
  results_exists: boolean;
  metrics_exists: boolean;
  config_snapshot_exists: boolean;
};

export type ModelSuggestion = {
  model_key: string;
  suggested_tags: string[];
};

export type ModelSuggestionsResponse = {
  models: ModelSuggestion[];
  note: string;
};
