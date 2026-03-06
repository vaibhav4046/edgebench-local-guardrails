type Props = {
  logs: Array<Record<string, unknown>>;
};

export function LiveLogs({ logs }: Props) {
  return (
    <section className="panel">
      <h2>Live Logs</h2>
      <div className="logbox">
        {logs.slice(-200).map((item, idx) => (
          <pre key={idx}>{JSON.stringify(item, null, 2)}</pre>
        ))}
      </div>
    </section>
  );
}
