import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

type Activity = {
  id: number;
  opportunity_id: number;
  activity_type: string;
  activity_at: string;
  notes?: string | null;
};

type Opportunity = {
  id: number;
  company_name?: string | null;
  person_name?: string | null;
};

type User = {
  id: number;
  name: string;
  role?: string;
};

const TYPE_OPTIONS = [
  { value: "call", label: "Llamada" },
  { value: "reunion_online", label: "Reunión en línea" },
  { value: "reunion_presencial", label: "Reunión presencial" },
  { value: "email", label: "Correo electrónico" }
];

const STAGE_OPTIONS = [
  { value: "", label: "Todas las etapas" },
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

export default function ActivitiesPage() {
  const { token, user } = useAuth();
  const [items, setItems] = useState<Activity[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [sellers, setSellers] = useState<User[]>([]);
  const [opportunityId, setOpportunityId] = useState("");
  const [activityType, setActivityType] = useState(TYPE_OPTIONS[0].value);
  const [activityAt, setActivityAt] = useState("");
  const [notes, setNotes] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"lista" | "agenda" | "calendario">("lista");
  const [filterSeller, setFilterSeller] = useState("");
  const [filterStage, setFilterStage] = useState("");
  const [calendarMonth, setCalendarMonth] = useState(() => new Date());
  const [selectedDay, setSelectedDay] = useState<string | null>(null);

  async function load() {
    const params = new URLSearchParams();
    if (user?.role !== "seller") {
      if (filterSeller) params.append("assigned_to_id", filterSeller);
      if (filterStage) params.append("stage", filterStage);
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    const data = await apiFetch<Activity[]>(`/api/activities${query}`, {
      token: token || undefined
    });
    setItems(data);
    const opps = await apiFetch<Opportunity[]>("/api/opportunities", { token: token || undefined });
    setOpportunities(opps);
    if (user?.role !== "seller") {
      const users = await apiFetch<User[]>("/api/users", { token: token || undefined });
      setSellers(users.filter((u) => u.role === "seller"));
    }
  }

  useEffect(() => {
    load();
  }, [filterSeller, filterStage]);

  function resetForm() {
    setOpportunityId("");
    setActivityType(TYPE_OPTIONS[0].value);
    setActivityAt("");
    setNotes("");
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;

    const payload = {
      opportunity_id: Number(opportunityId),
      activity_type: activityType,
      activity_at: activityAt ? new Date(activityAt).toISOString() : null,
      notes: notes || null
    };

    if (editingId) {
      await apiFetch(`/api/activities/${editingId}`, {
        method: "PATCH",
        token,
        body: JSON.stringify(payload)
      });
    } else {
      await apiFetch(`/api/activities`, {
        method: "POST",
        token,
        body: JSON.stringify(payload)
      });
    }

    resetForm();
    await load();
  }

  function opportunityLabel(id: number) {
    const opp = opportunities.find((o) => o.id === id);
    if (!opp) return `Oportunidad ${id}`;
    return opp.company_name || opp.person_name || `Oportunidad ${id}`;
  }

  function startEdit(activity: Activity) {
    setEditingId(activity.id);
    setOpportunityId(String(activity.opportunity_id));
    setActivityType(activity.activity_type);
    const date = new Date(activity.activity_at);
    setActivityAt(date.toISOString().slice(0, 16));
    setNotes(activity.notes || "");
  }

  function typeLabel(value: string) {
    return TYPE_OPTIONS.find((o) => o.value === value)?.label || value;
  }

  function formatDate(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  function toDateKey(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Sin fecha";
    return date.toISOString().slice(0, 10);
  }

  const agendaGroups = items.reduce<Record<string, Activity[]>>((acc, act) => {
    const key = toDateKey(act.activity_at);
    if (!acc[key]) acc[key] = [];
    acc[key].push(act);
    return acc;
  }, {});

  const monthStart = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1);
  const monthEnd = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 0);
  const startDay = monthStart.getDay();
  const daysInMonth = monthEnd.getDate();
  const cells = Array.from({ length: startDay + daysInMonth }, (_, idx) => {
    if (idx < startDay) return null;
    return idx - startDay + 1;
  });
  const monthKey = calendarMonth.toISOString().slice(0, 7);
  const monthActivities = items.filter((act) => toDateKey(act.activity_at).startsWith(monthKey));

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Actividades</h2>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-slate-100">
          Recargar
        </button>
      </div>

      <form onSubmit={handleSubmit} className="mb-4 rounded-lg border bg-white p-3 text-sm">
        <div className="mb-2 font-semibold">
          {editingId ? "Editar actividad" : "Nueva actividad"}
        </div>
        <div className="grid gap-2 md:grid-cols-4">
          <select
            className="rounded border px-2 py-1"
            value={opportunityId}
            onChange={(e) => setOpportunityId(e.target.value)}
            required
          >
            <option value="">Seleccionar oportunidad</option>
            {opportunities.map((opp) => (
              <option key={opp.id} value={opp.id}>
                {opportunityLabel(opp.id)}
              </option>
            ))}
          </select>
          <select
            className="rounded border px-2 py-1"
            value={activityType}
            onChange={(e) => setActivityType(e.target.value)}
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <input
            className="rounded border px-2 py-1"
            type="datetime-local"
            value={activityAt}
            onChange={(e) => setActivityAt(e.target.value)}
            required
          />
          <input
            className="rounded border px-2 py-1"
            placeholder="Notas"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <div className="mt-3 flex gap-2">
          <button className="rounded bg-indigo-600 px-3 py-1 text-xs text-white">
            {editingId ? "Actualizar" : "Crear"}
          </button>
          {editingId ? (
            <button
              type="button"
              onClick={resetForm}
              className="rounded border px-3 py-1 text-xs"
            >
              Cancelar
            </button>
          ) : null}
        </div>
      </form>

      {user?.role !== "seller" ? (
        <div className="mb-4 rounded-lg border bg-white p-3 text-sm">
          <div className="mb-2 font-semibold">Filtros (Manager)</div>
          <div className="grid gap-2 md:grid-cols-3">
            <select
              className="rounded border px-2 py-1"
              value={filterSeller}
              onChange={(e) => setFilterSeller(e.target.value)}
            >
              <option value="">Todos los vendedores</option>
              {sellers.map((seller) => (
                <option key={seller.id} value={seller.id}>
                  {seller.name}
                </option>
              ))}
            </select>
            <select
              className="rounded border px-2 py-1"
              value={filterStage}
              onChange={(e) => setFilterStage(e.target.value)}
            >
              {STAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => {
                setFilterSeller("");
                setFilterStage("");
              }}
              className="rounded border px-2 py-1 text-xs"
            >
              Limpiar filtros
            </button>
          </div>
        </div>
      ) : null}

      <div className="mb-3 flex gap-2 text-xs">
        <button
          onClick={() => setViewMode("lista")}
          className={`rounded border px-2 py-1 ${
            viewMode === "lista" ? "bg-slate-900 text-white" : "bg-white"
          }`}
        >
          Lista
        </button>
        <button
          onClick={() => setViewMode("agenda")}
          className={`rounded border px-2 py-1 ${
            viewMode === "agenda" ? "bg-slate-900 text-white" : "bg-white"
          }`}
        >
          Agenda
        </button>
        <button
          onClick={() => setViewMode("calendario")}
          className={`rounded border px-2 py-1 ${
            viewMode === "calendario" ? "bg-slate-900 text-white" : "bg-white"
          }`}
        >
          Calendario
        </button>
      </div>

      <div className="space-y-2">
        {viewMode === "lista"
          ? items.map((act) => (
              <div key={act.id} className="rounded border bg-white p-3 text-sm">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{typeLabel(act.activity_type)}</div>
                  <button
                    onClick={() => startEdit(act)}
                    className="rounded border px-2 py-1 text-xs"
                  >
                    Editar
                  </button>
                </div>
                <div className="text-xs text-slate-500">{formatDate(act.activity_at)}</div>
                <div className="text-xs text-slate-500">
                  {opportunityLabel(act.opportunity_id)}
                </div>
                {act.notes ? <div className="text-xs">{act.notes}</div> : null}
              </div>
            ))
          : viewMode === "agenda"
            ? Object.entries(agendaGroups).map(([day, acts]) => (
                <div key={day} className="rounded border bg-white p-3 text-sm">
                  <div className="mb-2 text-xs font-semibold text-slate-600">{day}</div>
                  <div className="space-y-2">
                    {acts.map((act) => (
                      <div key={act.id} className="rounded border px-2 py-2">
                        <div className="flex items-center justify-between">
                          <div className="font-medium">{typeLabel(act.activity_type)}</div>
                          <button
                            onClick={() => startEdit(act)}
                            className="rounded border px-2 py-1 text-xs"
                          >
                            Editar
                          </button>
                        </div>
                        <div className="text-xs text-slate-500">
                          {formatDate(act.activity_at)}
                        </div>
                        <div className="text-xs text-slate-500">
                          {opportunityLabel(act.opportunity_id)}
                        </div>
                        {act.notes ? <div className="text-xs">{act.notes}</div> : null}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            : (
                <div className="rounded border bg-white p-3 text-sm">
                  <div className="mb-2 flex items-center justify-between">
                    <button
                      onClick={() =>
                        setCalendarMonth(
                          new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1, 1)
                        )
                      }
                      className="rounded border px-2 py-1 text-xs"
                    >
                      {"<"} Mes anterior
                    </button>
                    <div className="text-sm font-semibold">
                      {calendarMonth.toLocaleString("es", { month: "long", year: "numeric" })}
                    </div>
                    <button
                      onClick={() =>
                        setCalendarMonth(
                          new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 1)
                        )
                      }
                      className="rounded border px-2 py-1 text-xs"
                    >
                      Mes siguiente {">"}
                    </button>
                  </div>
                  <div className="grid grid-cols-7 gap-2 text-xs">
                    {"Dom Lun Mar Mié Jue Vie Sáb".split(" ").map((d) => (
                      <div key={d} className="text-center font-semibold text-slate-500">
                        {d}
                      </div>
                    ))}
                    {cells.map((day, idx) => {
                      if (!day) return <div key={`empty-${idx}`} className="h-16" />;
                      const key = `${monthKey}-${String(day).padStart(2, "0")}`;
                      const count = monthActivities.filter(
                        (a) => toDateKey(a.activity_at) === key
                      ).length;
                      return (
                        <button
                          key={key}
                          onClick={() => setSelectedDay(key)}
                          className={`flex h-16 flex-col rounded border p-1 text-left ${
                            selectedDay === key ? "border-indigo-500 bg-indigo-50" : "bg-white"
                          }`}
                        >
                          <span className="text-xs font-semibold">{day}</span>
                          <span className="text-[10px] text-slate-500">{count} act.</span>
                        </button>
                      );
                    })}
                  </div>
                  {selectedDay ? (
                    <div className="mt-3 space-y-2">
                      <div className="text-xs font-semibold text-slate-600">
                        Actividades {selectedDay}
                      </div>
                      {items
                        .filter((a) => toDateKey(a.activity_at) === selectedDay)
                        .map((act) => (
                          <div key={act.id} className="rounded border px-2 py-2">
                            <div className="flex items-center justify-between">
                              <div className="font-medium">{typeLabel(act.activity_type)}</div>
                              <button
                                onClick={() => startEdit(act)}
                                className="rounded border px-2 py-1 text-xs"
                              >
                                Editar
                              </button>
                            </div>
                            <div className="text-xs text-slate-500">
                              {formatDate(act.activity_at)}
                            </div>
                            <div className="text-xs text-slate-500">
                              {opportunityLabel(act.opportunity_id)}
                            </div>
                            {act.notes ? <div className="text-xs">{act.notes}</div> : null}
                          </div>
                        ))}
                    </div>
                  ) : null}
                </div>
              )}
        {!items.length ? <div className="text-sm text-slate-400">Sin actividades</div> : null}
      </div>
    </div>
  );
}
