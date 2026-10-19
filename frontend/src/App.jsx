import { useEffect, useState } from "react";

// Placeholder page for Phase 1: confirms the frontend can reach the backend.
export default function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        return res.json();
      })
      .then(setHealth)
      .catch(() => setError("Can't reach the backend. Is it running on port 8000?"));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <h1 className="text-2xl font-semibold">DocReview</h1>
        <p className="mt-1 text-slate-500">AI-assisted quality checks for BA documents.</p>

        <div className="mt-6 text-sm">
          {!health && !error && <p className="text-slate-500">Checking backend…</p>}
          {error && <p className="text-red-700">✗ {error}</p>}
          {health && (
            <ul className="space-y-1">
              <li className="text-green-700">✓ Backend: connected</li>
              <li>Model: {health.model}</li>
              <li className={health.api_key_configured ? "text-green-700" : "text-amber-700"}>
                {health.api_key_configured
                  ? "✓ API key: configured"
                  : "! API key: not set yet (add it to .env; needed from Phase 4)"}
              </li>
            </ul>
          )}
        </div>
      </div>
    </main>
  );
}
