import { Link, Outlet } from "react-router-dom";

export function App() {
  return (
    <div className="shell">
      <header className="topbar">
        <h1>EdgeBench: Local LLM Benchmark</h1>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/run">Run Detail</Link>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
