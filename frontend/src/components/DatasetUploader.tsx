import { useRef } from "react";

type Props = {
  datasetPath: string;
  onDatasetPathChange: (path: string) => void;
  onUpload: (file: File) => Promise<void>;
};

export function DatasetUploader({ datasetPath, onDatasetPathChange, onUpload }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <section className="panel">
      <h2>Dataset</h2>
      <div className="row">
        <label className="grow">
          JSONL path
          <input value={datasetPath} onChange={(e) => onDatasetPathChange(e.target.value)} />
        </label>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="button button-secondary"
        >
          Upload JSONL
        </button>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept=".jsonl,.txt"
        hidden
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (file) {
            await onUpload(file);
          }
          e.currentTarget.value = "";
        }}
      />
    </section>
  );
}
