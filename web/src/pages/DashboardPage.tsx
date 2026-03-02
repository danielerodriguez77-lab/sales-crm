import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

const STAGE_LABELS: Record<string, string> = {
  lead_nuevo: "Lead Nuevo",
  calificado: "Calificado",
  contacto_seguimiento: "Contacto/Seguimiento",
  oferta_enviada: "Oferta Enviada",
  negociacion: "Negociación",
  ganado: "Ganado",
  facturacion: "Facturación",
  cobro_parcial: "Cobro Parcial",
  pagado_cerrado: "Pagado/Cerrado",
  perdido: "Perdido"
};

type Dashboard = {
  pipeline_by_stage: Record<string, number>;
  conversion_by_stage: Record<string, number>;
  avg_first_response_hours: number | null;
  avg_sales_cycle_days: number | null;
  quotes_sent: number;
  sales_won: number;
  revenue_won_by_month: { month: string; total: number }[];
  collected_by_month: { month: string; total: number }[];
  ranking: { seller: string; revenue: number; conversion: number; activity_volume: number; avg_ticket: number }[];
};

export default function DashboardPage() {
  const { token, user } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [tasks, setTasks] = useState<
    { id: number; title: string; status: string; due_at?: string | null }[]
  >([]);
  const [alerts, setAlerts] = useState<{ id: number; message: string; alert_type: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<Dashboard>("/api/dashboards/summary", {
        token: token || undefined
      });
      setData(res);
      if (user?.role === "seller") {
        const [taskData, alertData] = await Promise.all([
          apiFetch<typeof tasks>("/api/tasks", { token: token || undefined }),
          apiFetch<typeof alerts>("/api/alerts", { token: token || undefined })
        ]);
        setTasks(taskData.filter((t) => t.status === "open"));
        setAlerts(alertData);
      } else {
        setTasks([]);
        setAlerts([]);
      }
    } catch (err) {
      setError("No se pudo cargar el dashboard. Intenta recargar.");
    } finally {
      setLoading(false);
    }
  }

  async function markTaskDone(taskId: number) {
    if (!token) return;
    await apiFetch(`/api/tasks/${taskId}`, {
      method: "PATCH",
      token,
      body: JSON.stringify({ status: "done" })
    });
    await load();
  }

  useEffect(() => {
    if (!token) return;
    load();
  }, [token]);

  const pipelineData = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.pipeline_by_stage).map(([stage, value]) => ({
      stage: STAGE_LABELS[stage] || stage,
      value
    }));
  }, [data]);

  if (loading) return <div>Cargando...</div>;
  if (error) return <div className="text-sm text-red-600">{error}</div>;
  if (!data) return <div className="text-sm text-slate-500">Sin datos</div>;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Dashboard</h2>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-slate-100">
          Recargar
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded border bg-white p-3">
          <div className="text-xs text-slate-500">Tiempo primera respuesta</div>
          <div className="text-lg font-semibold">{data.avg_first_response_hours ?? "-"} h</div>
        </div>
        <div className="rounded border bg-white p-3">
          <div className="text-xs text-slate-500">Ciclo de venta</div>
          <div className="text-lg font-semibold">{data.avg_sales_cycle_days ?? "-"} días</div>
        </div>
        <div className="rounded border bg-white p-3">
          <div className="text-xs text-slate-500">Cotizaciones enviadas</div>
          <div className="text-lg font-semibold">{data.quotes_sent}</div>
        </div>
        <div className="rounded border bg-white p-3">
          <div className="text-xs text-slate-500">Ventas ganadas</div>
          <div className="text-lg font-semibold">{data.sales_won}</div>
        </div>
      </div>

      {user?.role === "seller" ? (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded border bg-white p-4">
            <h3 className="text-sm font-semibold">Recordatorios</h3>
            <ul className="mt-2 space-y-2 text-sm">
              {tasks.map((task) => (
                <li key={task.id} className="rounded border px-2 py-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{task.title}</div>
                      <div className="text-xs text-slate-500">{task.due_at || "-"}</div>
                    </div>
                    <button
                      onClick={() => markTaskDone(task.id)}
                      className="rounded border px-2 py-1 text-xs"
                    >
                      Hecho
                    </button>
                  </div>
                </li>
              ))}
              {!tasks.length ? (
                <li className="text-xs text-slate-400">Sin recordatorios</li>
              ) : null}
            </ul>
          </div>
          <div className="rounded border bg-white p-4">
            <h3 className="text-sm font-semibold">Alertas</h3>
            <ul className="mt-2 space-y-2 text-sm">
              {alerts.map((alert) => (
                <li key={alert.id} className="rounded border px-2 py-2">
                  <div className="font-medium">{alert.message}</div>
                  <div className="text-xs text-slate-500">{alert.alert_type}</div>
                </li>
              ))}
              {!alerts.length ? (
                <li className="text-xs text-slate-400">Sin alertas</li>
              ) : null}
            </ul>
          </div>
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded border bg-white p-4">
          <h3 className="text-sm font-semibold">Pipeline por etapa</h3>
          <div className="mt-3 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineData}>
                <XAxis dataKey="stage" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 space-y-1 text-xs text-slate-500">
            {pipelineData.map((row) => (
              <li key={row.stage} className="flex justify-between">
                <span>{row.stage}</span>
                <span>{row.value}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded border bg-white p-4">
          <h3 className="text-sm font-semibold">Conversión por etapa (%)</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {Object.entries(data.conversion_by_stage).map(([stage, value]) => (
              <li key={stage} className="flex justify-between">
                <span>{STAGE_LABELS[stage] || stage}</span>
                <span>{value}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded border bg-white p-4">
          <h3 className="text-sm font-semibold">Revenue ganado por mes</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {data.revenue_won_by_month.map((row) => (
              <li key={row.month} className="flex justify-between">
                <span>{row.month}</span>
                <span>{row.total}</span>
              </li>
            ))}
            {!data.revenue_won_by_month.length ? (
              <li className="text-xs text-slate-400">Sin datos</li>
            ) : null}
          </ul>
        </div>
        <div className="rounded border bg-white p-4">
          <h3 className="text-sm font-semibold">Cobros por mes</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {data.collected_by_month.map((row) => (
              <li key={row.month} className="flex justify-between">
                <span>{row.month}</span>
                <span>{row.total}</span>
              </li>
            ))}
            {!data.collected_by_month.length ? (
              <li className="text-xs text-slate-400">Sin datos</li>
            ) : null}
          </ul>
        </div>
      </div>

      <div className="mt-6 rounded border bg-white p-4">
        <h3 className="text-sm font-semibold">Ranking vendedores</h3>
        <table className="mt-2 w-full text-sm">
          <thead className="text-left text-xs text-slate-500">
            <tr>
              <th>Vendedor</th>
              <th>Revenue</th>
              <th>Conversión</th>
              <th>Actividades</th>
              <th>Ticket Promedio</th>
            </tr>
          </thead>
          <tbody>
            {data.ranking.map((row, idx) => (
              <tr key={idx} className="border-t">
                <td className="py-2">{row.seller}</td>
                <td>{row.revenue}</td>
                <td>{row.conversion}%</td>
                <td>{row.activity_volume}</td>
                <td>{row.avg_ticket}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
