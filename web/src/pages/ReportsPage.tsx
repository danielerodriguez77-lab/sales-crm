import { useState } from "react";
import { useAuth } from "../lib/AuthContext";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function downloadCsv(path: string, token: string) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = path.split("/").pop() || "reporte.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export default function ReportsPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);

  async function handle(path: string) {
    if (!token) return;
    setLoading(true);
    await downloadCsv(path, token);
    setLoading(false);
  }

  return (
    <div>
      <h2 className="text-xl font-semibold">Reportes</h2>
      <div className="mt-4 space-y-2">
        <button
          disabled={loading}
          onClick={() => handle("/api/reports/seller-performance")}
          className="rounded border px-3 py-2 text-sm"
        >
          Descargar desempeño vendedores
        </button>
        <button
          disabled={loading}
          onClick={() => handle("/api/reports/pipeline-snapshot")}
          className="rounded border px-3 py-2 text-sm"
        >
          Descargar pipeline snapshot
        </button>
        <button
          disabled={loading}
          onClick={() => handle("/api/reports/aging")}
          className="rounded border px-3 py-2 text-sm"
        >
          Descargar aging report
        </button>
      </div>
    </div>
  );
}
