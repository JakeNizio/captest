const API_BASE = import.meta.env.VITE_BACKEND_URL || "http://localhost:8080";

export default function App() {
  return (
    <main className="page">
      <p className="eyebrow">Phase 1 scaffold</p>
      <h1>AI Agent Dashboard</h1>
      <p>
        Business UI stub. Control plane health:{" "}
        <code>{API_BASE}/health</code>
      </p>
    </main>
  );
}
