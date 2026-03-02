import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

const STAGES = [
  { value: "lead_nuevo", label: "Lead Nuevo" },
  { value: "calificado", label: "Calificado" },
  { value: "contacto_seguimiento", label: "Contacto/Seguimiento" },
  { value: "oferta_enviada", label: "Oferta Enviada" },
  { value: "negociacion", label: "Negociación" },
  { value: "ganado", label: "Ganado" },
  { value: "facturacion", label: "Facturación" },
  { value: "cobro_parcial", label: "Cobro Parcial" },
  { value: "pagado_cerrado", label: "Pagado/Cerrado" },
  { value: "perdido", label: "Perdido" }
];

type Opportunity = {
  id: number;
  company_name?: string | null;
  person_name?: string | null;
  stage: string;
  estimated_value?: number | null;
  assigned_to_id?: number | null;
  next_action_at?: string | null;
  no_next_action?: boolean;
};

export default function PipelinePage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const data = await apiFetch<Opportunity[]>("/api/opportunities", { token: token || undefined });
    setItems(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  const grouped = useMemo(() => {
    const map: Record<string, Opportunity[]> = {};
    STAGES.forEach((s) => (map[s.value] = []));
    items.forEach((opp) => {
      if (!map[opp.stage]) map[opp.stage] = [];
      map[opp.stage].push(opp);
    });
    return map;
  }, [items]);

  async function updateStage(id: number, stage: string) {
    await apiFetch(`/api/opportunities/${id}`, {
      method: "PATCH",
      token: token || undefined,
      body: JSON.stringify({ stage })
    });
    await load();
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Pipeline</h2>
        <button
          onClick={load}
          className="rounded border px-3 py-1 text-sm hover:bg-slate-100"
        >
          Recargar
        </button>
      </div>
      {loading ? <div>Cargando...</div> : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {STAGES.map((stage) => (
          <div key={stage.value} className="rounded-lg border bg-white p-3">
            <div className="mb-2 text-sm font-semibold text-slate-700">{stage.label}</div>
            <div className="space-y-2">
              {grouped[stage.value]?.map((opp) => (
                <div key={opp.id} className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="text-sm font-medium">
                    {opp.company_name || opp.person_name || `Oportunidad ${opp.id}`}
                  </div>
                  <div className="text-xs text-slate-500">
                    Valor: {opp.estimated_value ?? 0}
                  </div>
                  <select
                    className="mt-2 w-full rounded border px-2 py-1 text-xs"
                    value={opp.stage}
                    onChange={(e) => updateStage(opp.id, e.target.value)}
                  >
                    {STAGES.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
              {!grouped[stage.value]?.length ? (
                <div className="text-xs text-slate-400">Sin oportunidades</div>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
