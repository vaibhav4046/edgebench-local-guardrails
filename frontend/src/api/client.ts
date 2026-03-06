import type {
  ModelSuggestionsResponse,
  RecordResponse,
  ResultRunInfo,
  RunJob,
  RunRequest,
  SummaryResponse,
} from "../types/api";

const API_BASE = "http://127.0.0.1:8000/api/v1";

async function jsonRequest<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<Record<string, unknown>> {
  return jsonRequest(`${API_BASE}/health`);
}

export async function getModelSuggestions(): Promise<ModelSuggestionsResponse> {
  return jsonRequest(`${API_BASE}/models/suggestions`);
}

export async function uploadDataset(file: File): Promise<{ ok: boolean; path: string }> {
  const form = new FormData();
  form.append("file", file);
  return jsonRequest(`${API_BASE}/datasets/upload`, { method: "POST", body: form });
}

export async function createRun(payload: RunRequest): Promise<{ ok: boolean; job: RunJob }> {
  return jsonRequest(`${API_BASE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listRuns(): Promise<{ ok: boolean; jobs: RunJob[] }> {
  return jsonRequest(`${API_BASE}/runs`);
}

export async function listResultRuns(): Promise<{ ok: boolean; runs: ResultRunInfo[] }> {
  return jsonRequest(`${API_BASE}/results`);
}

export async function getRun(runId: string): Promise<{ ok: boolean; job: RunJob }> {
  return jsonRequest(`${API_BASE}/runs/${runId}`);
}

export async function cancelRun(runId: string): Promise<{ ok: boolean; message: string }> {
  return jsonRequest(`${API_BASE}/runs/${runId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function getSummary(runId: string): Promise<SummaryResponse> {
  return jsonRequest(`${API_BASE}/results/${runId}/summary`);
}

export async function getRecords(runId: string, limit = 300, offset = 0): Promise<RecordResponse> {
  return jsonRequest(`${API_BASE}/results/${runId}/records?limit=${limit}&offset=${offset}`);
}

export function eventsUrl(runId: string): string {
  return `${API_BASE}/runs/${runId}/events`;
}

export function exportCsvUrl(runId: string): string {
  return `${API_BASE}/results/${runId}/export.csv`;
}

export function exportJsonUrl(runId: string): string {
  return `${API_BASE}/results/${runId}/export.json`;
}
