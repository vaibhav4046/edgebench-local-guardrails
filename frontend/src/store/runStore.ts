import { create } from "zustand";

import {
  cancelRun,
  createRun,
  eventsUrl,
  getRecords,
  getSummary,
  listResultRuns,
  listRuns,
  uploadDataset,
} from "../api/client";
import type { ResultRunInfo, RunEvent, RunJob, RunRequest } from "../types/api";

type State = {
  runs: RunJob[];
  resultRuns: ResultRunInfo[];
  selectedRunId: string | null;
  summary: Record<string, unknown> | null;
  records: Array<Record<string, unknown>>;
  logs: RunEvent[];
  loading: boolean;
  error: string | null;
  connected: boolean;
  eventSource: EventSource | null;
  datasetPath: string;
  setDatasetPath: (value: string) => void;
  refreshRuns: () => Promise<void>;
  refreshResultRuns: () => Promise<void>;
  startRun: (payload: RunRequest) => Promise<void>;
  cancelRunById: (runId: string) => Promise<void>;
  selectRun: (runId: string) => Promise<void>;
  fetchSummaryAndRecords: (runId: string) => Promise<void>;
  connectEvents: (runId: string) => void;
  disconnectEvents: () => void;
  uploadDatasetFile: (file: File) => Promise<void>;
};

export const useRunStore = create<State>((set, get) => ({
  runs: [],
  resultRuns: [],
  selectedRunId: null,
  summary: null,
  records: [],
  logs: [],
  loading: false,
  error: null,
  connected: false,
  eventSource: null,
  datasetPath: "data/smoke_prompts_10.jsonl",

  setDatasetPath: (value) => set({ datasetPath: value }),

  refreshRuns: async () => {
    set({ loading: true, error: null });
    try {
      const data = await listRuns();
      set({ runs: data.jobs, loading: false });
    } catch (error) {
      set({ error: String(error), loading: false });
    }
  },

  refreshResultRuns: async () => {
    try {
      const data = await listResultRuns();
      set({ resultRuns: data.runs });
    } catch {
      set({ resultRuns: [] });
    }
  },

  startRun: async (payload) => {
    set({ loading: true, error: null });
    try {
      const data = await createRun(payload);
      const jobId = data.job.job_id;
      set((state) => ({
        runs: [data.job, ...state.runs],
        selectedRunId: jobId,
        logs: [],
        loading: false,
      }));
      get().connectEvents(jobId);
      await Promise.all([get().refreshRuns(), get().refreshResultRuns()]);
    } catch (error) {
      set({ error: String(error), loading: false });
    }
  },

  cancelRunById: async (runId) => {
    try {
      await cancelRun(runId);
      await get().refreshRuns();
    } catch (error) {
      set({ error: String(error) });
    }
  },

  selectRun: async (runId) => {
    set({ selectedRunId: runId, logs: [] });
    await get().fetchSummaryAndRecords(runId);
    const inJobs = get().runs.some((item) => item.job_id === runId);
    if (inJobs) {
      get().connectEvents(runId);
    } else {
      get().disconnectEvents();
    }
  },

  fetchSummaryAndRecords: async (runId) => {
    try {
      const [summary, records] = await Promise.all([getSummary(runId), getRecords(runId)]);
      set({ summary, records: records.items });
    } catch {
      set({ summary: null, records: [] });
    }
  },

  connectEvents: (runId) => {
    get().disconnectEvents();
    const source = new EventSource(eventsUrl(runId));
    source.onopen = () => set({ connected: true });
    source.onerror = () => set({ connected: false });
    source.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as RunEvent;
        set((state) => ({ logs: [...state.logs, parsed] }));
        if (parsed.event === "progress") {
          get().refreshRuns();
        }
        if (parsed.event === "completed" || parsed.event === "canceled") {
          get().refreshRuns();
          get().refreshResultRuns();
          get().fetchSummaryAndRecords(runId);
        }
      } catch {
        // Ignore invalid SSE lines.
      }
    };
    set({ eventSource: source });
  },

  disconnectEvents: () => {
    const source = get().eventSource;
    if (source) {
      source.close();
    }
    set({ eventSource: null, connected: false });
  },

  uploadDatasetFile: async (file) => {
    set({ loading: true, error: null });
    try {
      const response = await uploadDataset(file);
      set({ datasetPath: response.path, loading: false });
    } catch (error) {
      set({ error: String(error), loading: false });
    }
  },
}));
