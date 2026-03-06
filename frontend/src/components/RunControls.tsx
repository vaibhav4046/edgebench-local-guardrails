type Props = {
  onStart: () => Promise<void>;
  onCancel: () => Promise<void>;
  canCancel: boolean;
};

export function RunControls({ onStart, onCancel, canCancel }: Props) {
  return (
    <section className="panel">
      <h2>Run Controls</h2>
      <div className="row">
        <button className="button" onClick={() => void onStart()}>
          Start Run
        </button>
        <button className="button button-danger" onClick={() => void onCancel()} disabled={!canCancel}>
          Stop Run
        </button>
      </div>
    </section>
  );
}
