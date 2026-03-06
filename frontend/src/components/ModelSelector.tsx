import type { ModelOverride } from "../types/api";

type Props = {
  models: ModelOverride[];
  suggestionsByModelKey?: Record<string, string[]>;
  onChange: (models: ModelOverride[]) => void;
};

export function ModelSelector({ models, suggestionsByModelKey = {}, onChange }: Props) {
  const update = (index: number, key: keyof ModelOverride, value: string | boolean) => {
    const next = [...models];
    next[index] = { ...next[index], [key]: value } as ModelOverride;
    onChange(next);
  };

  return (
    <section className="panel">
      <h2>Models + Tags</h2>
      <p className="muted">Choose logical models and local Ollama tags (quantized variants allowed).</p>
      <div className="model-grid">
        {models.map((model, idx) => (
          <div key={`${model.model_key}-${idx}`} className="model-card">
            <label>
              <input
                type="checkbox"
                checked={model.enabled}
                onChange={(e) => update(idx, "enabled", e.target.checked)}
              />
              <span>{model.model_key}</span>
            </label>
            <label>
              Ollama tag
              <input
                value={model.tag}
                onChange={(e) => update(idx, "tag", e.target.value)}
                placeholder="e.g. mistral:7b-instruct-q4_K_M"
                list={`tags-${idx}`}
              />
              <datalist id={`tags-${idx}`}>
                {(suggestionsByModelKey[model.model_key] || []).map((tag) => (
                  <option key={tag} value={tag} />
                ))}
              </datalist>
            </label>
            <label>
              Ollama base URL
              <input
                value={model.base_url}
                onChange={(e) => update(idx, "base_url", e.target.value)}
                placeholder="http://127.0.0.1:11434"
              />
            </label>
          </div>
        ))}
      </div>
    </section>
  );
}
