import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
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

type Opportunity = {
  id: number;
  company_name?: string | null;
  person_name?: string | null;
  stage: string;
  estimated_value?: number | null;
  next_action_at?: string | null;
  no_next_action?: boolean;
};

export default function OpportunitiesPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Opportunity[]>([]);
  const [name, setName] = useState("");
  const [value, setValue] = useState(0);
  const [nextActionAt, setNextActionAt] = useState("");

  async function load() {
    const data = await apiFetch<Opportunity[]>("/api/opportunities", { token: token || undefined });
    setItems(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function createOpportunity(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    await apiFetch("/api/opportunities", {
      method: "POST",
      token,
      body: JSON.stringify({
        record_type: "lead",
        company_name: name,
        estimated_value: value,
        next_action_at: nextActionAt ? new Date(nextActionAt).toISOString() : null,
        no_next_action: !nextActionAt
      })
    });
    setName("");
    setValue(0);
    setNextActionAt("");
    await load();
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Leads y Oportunidades</h2>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-slate-100">
          Recargar
        </button>
      </div>
      <form onSubmit={createOpportunity} className="mb-4 rounded-lg border bg-white p-3 text-sm">
        <div className="mb-2 font-semibold">Nuevo lead</div>
        <div className="grid gap-2 md:grid-cols-3">
          <input
            className="rounded border px-2 py-1"
            placeholder="Empresa"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="rounded border px-2 py-1"
            type="number"
            placeholder="Valor estimado"
            value={value}
            onChange={(e) => setValue(Number(e.target.value))}
          />
          <input
            className="rounded border px-2 py-1"
            type="datetime-local"
            value={nextActionAt}
            onChange={(e) => setNextActionAt(e.target.value)}
          />
        </div>
        <button className="mt-3 rounded bg-indigo-600 px-3 py-1 text-xs text-white">Crear</button>
      </form>
      <div className="overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Nombre</th>
              <th className="px-3 py-2">Etapa</th>
              <th className="px-3 py-2">Valor</th>
              <th className="px-3 py-2">Próxima acción</th>
            </tr>
          </thead>
          <tbody>
            {items.map((opp) => (
              <tr key={opp.id} className="border-t">
                <td className="px-3 py-2">
                  <Link className="text-indigo-600" to={`/oportunidades/${opp.id}`}>
                    {opp.company_name || opp.person_name || `Oportunidad ${opp.id}`}
                  </Link>
                </td>
                <td className="px-3 py-2">{STAGE_LABELS[opp.stage] || opp.stage}</td>
                <td className="px-3 py-2">{opp.estimated_value ?? 0}</td>
                <td className="px-3 py-2">
                  {opp.no_next_action ? "Sin próxima acción" : opp.next_action_at || "-"}
                </td>
              </tr>
            ))}
            {!items.length ? (
              <tr>
                <td className="px-3 py-6 text-center text-slate-400" colSpan={4}>
                  Sin registros
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
